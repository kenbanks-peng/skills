"""Saved launch interface tests with real Git and controlled external CLIs."""

import fcntl
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FAKE = r"""#!PYTHON
import json, os, subprocess, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
root = Path(os.environ["CASE_ROOT"])
repo = root / "repo"
worker = root / "worker"
mode = os.environ.get("MODE", "")
with (root / "calls").open("a") as out:
    out.write(json.dumps([name, *args]) + "\n")
def git(*args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
if name == "aven":
    if mode == "base-move-context":
        git("commit", "--allow-empty", "-qm", "new base")
    print(json.dumps({
        "task": {"id": "task-id", "display_ref": "APP-TEST", "status": "active",
                 "deleted": False, "title": "Literal `code` $(touch SENTINEL) \\path\nnext",
                 "description": "Use $HOME and `backticks` literally\nsecond line"},
        "project": {"key": "project"}, "workspace": {"key": "default"},
        "notes": [{"body": "Keep this durable context"}]
    }))
elif name == "workmux":
    if args[0] == "add":
        (root / "sandboxed").write_text("yes" if "--sandbox" in args else "no")
        branch = args[1]
        base = args[args.index("--base") + 1]
        git("worktree", "add", "-b", branch, str(worker), base)
        generated = worker / ".workmux"
        generated.mkdir()
        (generated / "PROMPT-test.md").write_text(Path(args[args.index("-P") + 1]).read_text())
        if mode == "base-move-add":
            git("commit", "--allow-empty", "-qm", "moved during add")
        if mode == "partial":
            print("created pane-1 container-1")
            sys.stderr.write("startup failed after creation")
            sys.exit(7)
    elif args[0] == "list":
        if mode == "base-move-list" and not worker.exists():
            git("commit", "--allow-empty", "-qm", "moved before add")
        rows = []
        if worker.exists():
            rows = [{"handle": "dispatch-app-test", "is_main": False,
                     "path": str(worker), "branch": "dispatch/app-test"}]
        print(json.dumps(rows))
    elif args[0] == "wait":
        if mode == "unsupported-wait":
            sys.stderr.write("unexpected argument --status")
            sys.exit(2)
        if mode in ("fast-done", "missing-ui"):
            sys.stderr.write("working status was never observed")
            sys.exit(3)
    elif args[0] == "status":
        agent = {"worktree": "dispatch-app-test", "project_path": str(repo),
                 "pane_id": "pane-CHANGED" if mode == "changed-ui" else "pane-1",
                 "agent_kind": None if mode.startswith("process-") else "pi",
                 "session": "session-1", "window_name": "worker",
                 "workdir": str(worker) if (root / "sandboxed").read_text() == "no" else "/guest/worker",
                 "status": "done" if mode == "fast-done" else "working"}
        agents = [] if mode == "missing-ui" else [agent]
        if mode == "ambiguous-ui":
            agents.append(dict(agent, pane_id="pane-2"))
        print(json.dumps({"context": {"backend": "herdr", "instance": "socket-1"},
                          "agents": agents, "target_errors": []}))
    else:
        sys.exit(9)
elif name in ("docker", "container", "podman"):
    if args[0] in ("ps", "list"):
        ids = ["container-1", "container-2"] if mode == "ambiguous-container" else ["container-1"]
        if name == "container":
            print(json.dumps([{"configuration": {"id": identity}} for identity in ids]))
        else:
            print("\n".join(ids))
    elif args[0] == "exec":
        processes = [{"pid": 3, "start_ticks": "100", "exe": "/usr/bin/node",
                      "argv": ["pi"], "cwd": "/guest/worker", "kind": "pi"}]
        if mode == "process-missing":
            processes = []
        elif mode == "process-ambiguous":
            processes.append(dict(processes[0], pid=4))
        elif mode == "process-wrong-root":
            processes[0]["cwd"] = "/other/worker"
        elif mode == "process-error":
            sys.exit(7)
        print(json.dumps(processes))
    elif args[0] == "inspect":
        source = "/wrong-host" if mode == "wrong-mount" else str(worker)
        if name == "container":
            print(json.dumps([{"configuration": {"id": args[1], "mounts": [
                {"source": source, "destination": "/guest/worker"}]},
                "status": {"state": "running"}}]))
        else:
            print(json.dumps([{"Id": args[1], "State": {"Status": "running"},
                             "Mounts": [{"Type": "bind", "Source": source,
                                         "Destination": "/guest/worker"}]}]))
else:
    sys.exit(9)
"""


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.env.update(
            CASE_ROOT=str(self.root),
            HERDR_ENV="1",
            MODE="",
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Test",
            GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Test",
            GIT_COMMITTER_EMAIL="test@example.invalid",
            PYTHONDONTWRITEBYTECODE="1",
        )
        binary = self.root / "bin"
        binary.mkdir()
        for name in ("aven", "workmux", "docker", "container", "podman"):
            path = binary / name
            path.write_text(FAKE.replace("#!PYTHON", "#!" + sys.executable))
            path.chmod(0o755)
        self.env["PATH"] = str(binary) + os.pathsep + self.env["PATH"]
        self.env["HOME"] = str(self.root)
        config = self.root / ".config/workmux/agents.linux.yaml"
        config.parent.mkdir(parents=True)
        config.write_text("agent: pi\nsandbox:\n  enabled: true\n")
        self.git("init", "-b", "main")
        (self.repo / "file").write_text("base")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.record = self.repo / ".git/dispatch-workers/APP-TEST/worker.json"

    def git(self, *args):
        result = subprocess.run(
            ["git", "-C", str(self.repo), *args],
            env=self.env,
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()

    def cli(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "dispatch.py"), *args],
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stdout + result.stderr
        )
        data = json.loads(result.stdout)
        self.assertIs(data["ok"], ok)
        return data

    def launch(self, *extra, ok=True):
        return self.cli(
            "launch",
            "APP-TEST",
            "--base",
            "main",
            "--scope",
            "src/",
            "--check",
            '["python3", "-m", "unittest"]',
            *extra,
            ok=ok,
        )

    def calls(self):
        path = self.root / "calls"
        return (
            [json.loads(line) for line in path.read_text().splitlines()]
            if path.exists()
            else []
        )

    def adds(self):
        return [call for call in self.calls() if call[:2] == ["workmux", "add"]]

    def test_literal_prompt_default_routing_and_saved_identity(self):
        data = self.launch()
        saved = json.loads(self.record.read_text())
        self.assertEqual(saved, data)
        self.assertEqual(data["launch_base"], self.base)
        self.assertEqual(data["repo"], str(self.repo))
        self.assertEqual(data["agent_type"], "pi")
        self.assertEqual(data["container"]["id"], "container-1")
        self.assertEqual(data["worker_worktree"], "/guest/worker")
        self.assertEqual(data["ui"]["agents"][0]["pane_id"], "pane-1")
        self.assertEqual(data["routing"], {})
        self.assertEqual(self.calls()[0], ["aven", "context", "APP-TEST", "--json"])
        prompt = Path(data["prompt"]).read_text()
        self.assertIn("$(touch SENTINEL)", prompt)
        self.assertIn("`backticks`", prompt)
        self.assertIn("Keep this durable context", prompt)
        self.assertFalse((self.repo / "SENTINEL").exists())
        self.assertTrue(Path(data["prompts"][0]["archive_path"]).exists())
        self.assertFalse(Path(data["prompt"]).is_relative_to(self.root / "worker"))
        self.assertIn("--sandbox", self.adds()[0])
        self.assertIn("agents.linux.yaml", data["config"])

    def test_null_agent_kind_uses_exact_container_process_evidence(self):
        self.env["MODE"] = "process-pi"
        data = self.launch("--runtime", "docker")
        self.assertEqual(data["agent_type"], "pi")
        event = data["events"][-1]
        self.assertIsNone(event["workmux_status"]["agents"][0]["agent_kind"])
        self.assertEqual(event["agent_processes"][0]["pid"], 3)
        self.assertIn(["docker", "exec", "container-1"], [c[:3] for c in self.calls()])
        self.env["MODE"] = ""
        resumed = self.cli("inspect", "APP-TEST", "--resume")
        self.assertEqual(resumed["agent_type"], "pi")

    def test_null_kind_process_probe_uses_exact_apple_container(self):
        self.env["MODE"] = "process-pi"
        data = self.launch("--runtime", "apple-container")
        self.assertEqual(data["agent_type"], "pi")
        self.assertIn(
            ["container", "exec", "container-1"], [c[:3] for c in self.calls()]
        )

    def test_null_kind_process_probe_uses_exact_podman_container(self):
        self.env["MODE"] = "process-pi"
        data = self.launch("--runtime", "podman")
        self.assertEqual(data["agent_type"], "pi")
        self.assertIn(["podman", "exec", "container-1"], [c[:3] for c in self.calls()])

    def test_null_agent_kind_without_unique_process_fails_closed(self):
        for mode in (
            "process-missing",
            "process-ambiguous",
            "process-wrong-root",
            "process-error",
        ):
            with self.subTest(mode=mode):
                self.env["MODE"] = mode
                if self.record.exists():
                    self.cli("inspect", "APP-TEST", "--resume", ok=False)
                else:
                    self.launch(ok=False)
                self.assertEqual(len(self.adds()), 1)
                self.assertTrue((self.root / "worker").exists())

    def test_fast_completion_does_not_require_observing_working(self):
        self.env["MODE"] = "fast-done"
        data = self.launch()
        self.assertIn("wait_error", data["events"][0])
        self.assertEqual(
            data["events"][0]["workmux_status"]["agents"][0]["status"], "done"
        )

    def test_partial_launch_is_saved_and_retry_only_observes(self):
        self.env["MODE"] = "partial"
        data = self.launch(ok=False)
        self.assertIn("startup failed", data["events"][0]["launch_error"])
        self.assertIn("created pane-1 container-1", data["events"][0]["launch_error"])
        self.assertEqual(data["container"]["id"], "container-1")
        self.assertTrue(Path(data["prompt"]).exists())
        self.assertTrue(Path(data["prompts"][0]["archive_path"]).exists())
        self.env["MODE"] = ""
        resumed = self.cli("launch", "APP-TEST")
        self.assertEqual(len(self.adds()), 1)
        self.assertEqual(resumed["launch_base"], self.base)
        self.assertEqual(len(resumed["events"]), 2)

    def test_missing_or_ambiguous_identity_never_starts_replacement(self):
        for mode in (
            "ambiguous-ui",
            "ambiguous-container",
            "wrong-mount",
            "missing-ui",
        ):
            with self.subTest(mode=mode):
                if self.record.exists():
                    # Use the retained worker for each subsequent observation.
                    self.env["MODE"] = mode
                    data = self.cli("inspect", "APP-TEST", "--resume", ok=False)
                else:
                    self.env["MODE"] = mode
                    data = self.launch(ok=False)
                self.assertEqual(len(self.adds()), 1)
                self.assertTrue(data["events"][-1].get("error"))
                self.assertTrue((self.root / "worker/.git").exists())
                self.assertTrue(list(self.record.parent.glob("prompt-*.md")))

    def test_changed_identity_blocks_resume(self):
        self.launch()
        self.env["MODE"] = "changed-ui"
        data = self.cli("inspect", "APP-TEST", "--resume", ok=False)
        self.assertIn("identity changed", data["error"])
        self.assertEqual(data["ui"]["agents"][0]["pane_id"], "pane-1")
        self.assertEqual(
            data["events"][-1]["ui"]["agents"][0]["pane_id"], "pane-CHANGED"
        )
        self.assertEqual(len(self.adds()), 1)

    def test_unsupported_cli_requires_explicit_troubleshooting(self):
        self.env["MODE"] = "unsupported-wait"
        data = self.launch(ok=False)
        self.assertIn("compatibility troubleshooting", data["error"])
        self.assertEqual(data["container"]["id"], "container-1")
        self.env["MODE"] = ""
        self.cli("launch", "APP-TEST")
        self.assertEqual(len(self.adds()), 1)

    def test_missing_default_config_never_falls_back(self):
        (self.root / ".config/workmux/agents.linux.yaml").unlink()
        self.launch(ok=False)
        self.assertEqual(self.adds(), [])
        self.assertFalse(self.record.exists())

    def test_partial_launch_keeps_both_ui_and_container_observations(self):
        self.env["MODE"] = "missing-ui"
        data = self.launch(ok=False)
        event = data["events"][-1]
        self.assertEqual(event["workmux_status"]["agents"], [])
        self.assertEqual(event["containers"][0]["id"], "container-1")
        self.assertTrue(event["prompts"][0]["archive_path"])

    def test_base_move_during_add_still_starts_at_captured_sha(self):
        self.env["MODE"] = "base-move-add"
        data = self.launch()
        self.assertNotEqual(self.git("rev-parse", "main"), self.base)
        self.assertEqual(self.git("rev-parse", data["branch"]), self.base)
        argv = self.adds()[0]
        self.assertEqual(argv[argv.index("--base") + 1], self.base)

    def test_stale_launch_does_not_create_worker(self):
        self.env["MODE"] = "base-move-list"
        data = self.launch(ok=False)
        self.assertIn("Base moved", data["error"])
        self.assertEqual(self.adds(), [])
        self.assertTrue(Path(data["prompt"]).exists())
        self.cli("launch", "APP-TEST", ok=False)
        self.assertEqual(self.adds(), [])

    def test_local_requires_explicit_approval(self):
        self.launch("--runtime", "local", ok=False)
        self.assertEqual(self.adds(), [])
        config = self.root / "local.yaml"
        config.write_text("agent: pi\nsandbox:\n  enabled: false\n")
        data = self.launch(
            "--runtime", "local", "--allow-local", "--config", str(config)
        )
        self.assertIsNone(data["container"])
        self.assertEqual(data["worker_worktree"], str(self.root / "worker"))
        self.assertNotIn("--sandbox", self.adds()[0])

    def test_macos_config_requires_approval_even_with_sandbox_runtime(self):
        config = self.root / "agents.macos.yaml"
        config.write_text("agent: pi")
        self.launch("--config", str(config), ok=False)
        self.assertEqual(self.adds(), [])

    def test_serialization_blocks_creation(self):
        with (self.repo / ".git/dispatch.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.launch(ok=False)
        self.assertEqual(self.calls(), [])

    def test_existing_branch_without_record_blocks_creation(self):
        self.git("branch", "dispatch/app-test")
        self.launch(ok=False)
        self.assertEqual(self.adds(), [])

    def test_routing_override_is_saved_and_reused(self):
        data = self.launch("--workspace", "explicit")
        self.assertEqual(data["routing"], {"workspace": "explicit"})
        self.assertIn("--workspace", self.calls()[0])
        self.cli("inspect", "APP-TEST", "--resume")
        self.assertEqual(len(self.adds()), 1)
        self.assertEqual(
            [call for call in self.calls() if call[0] == "aven"][-1],
            ["aven", "context", "APP-TEST", "--json", "--workspace", "explicit"],
        )

    def test_inspect_is_read_only_and_assignment_cannot_change(self):
        self.launch()
        before = self.record.read_bytes()
        self.cli("inspect", "APP-TEST")
        self.assertEqual(self.record.read_bytes(), before)
        self.cli("launch", "APP-TEST", "--base", "other", ok=False)
        self.assertEqual(self.record.read_bytes(), before)
        self.assertEqual(len(self.adds()), 1)


if __name__ == "__main__":
    unittest.main()
