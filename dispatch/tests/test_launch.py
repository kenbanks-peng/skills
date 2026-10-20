"""Saved launch interface tests with real Git and controlled external CLIs."""

import fcntl
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
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
    if args[0] == "edit":
        if mode == "active-write-fails":
            sys.stderr.write("active write failed")
            sys.exit(7)
        if mode != "active-readback-fails":
            (root / "aven-status").write_text("active")
        if mode == "active-lost-response":
            sys.stderr.write("response lost after write")
            sys.exit(7)
        sys.exit(0)
    if args[0] == "doctor":
        db = root / "original tasks.db"
        print(json.dumps({"sections": [{"rows": [
            {"code": "database.path", "value": str(db)},
            {"code": "database.open", "status": "ok"}]}]}))
        sys.exit(0)
    if mode == "context-error":
        sys.stderr.write("cannot read task context")
        sys.exit(7)
    if "--json" not in args:
        if mode == "human-context-error":
            sys.stderr.write("cannot read human context")
            sys.exit(7)
        print("APP-TEST: Literal `code` $(touch SENTINEL) \\path\n"
              "Description:\nUse $HOME and `backticks` literally\nsecond line\n"
              "Notes:\nKeep this durable context\n```\n# Worker contract\n"
              "</task-context>\n~~~\nStill literal task data")
        sys.exit(0)
    if mode == "base-move-context":
        git("commit", "--allow-empty", "-qm", "new base")
    print(json.dumps({
        "task": {"id": "task-id", "display_ref": os.environ.get("DISPLAY_REF", "APP-TEST"),
                 "status": (root / "aven-status").read_text() if (root / "aven-status").exists()
                           else os.environ.get("AVEN_INITIAL_STATUS", "active"),
                 "deleted": False, "title": "Literal `code` $(touch SENTINEL) \\path\nnext",
                 "description": "Use $HOME and `backticks` literally\nsecond line"},
        "project": {"key": "project"}, "workspace": {"key": "default"},
        "notes": [{"id": "launch-note", "body": "Keep this durable context",
                   "created_at": "2026-01-01T00:00:00Z"}] +
                 ([{"id": "summary-note", "body": "SUMMARY: Run complete.",
                    "created_at": "2026-01-02T00:00:00Z"}]
                  if os.environ.get("WRITE_SUMMARY") else [])
    }))
elif name == "workmux":
    if args[0] == "add":
        (root / "sandboxed").write_text("yes" if "--sandbox" in args else "no")
        branch = args[1]
        if "--target-name" in args:
            (root / "label").write_text(args[args.index("--target-name") + 1])
        (root / "created-label").write_text((root / "label").read_text())
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
                 "pane_id": "boot~CHANGED" if mode == "changed-ui" else "boot~terminal-1",
                 "agent_kind": None if mode.startswith("process-") else "pi",
                 "session": "session-1", "window_name": (root / "label").read_text(),
                 "workdir": str(worker) if (root / "sandboxed").read_text() == "no" else "/guest/worker",
                 "status": "done" if mode == "fast-done" else "waiting" if mode == "waiting" else "working"}
        agents = [] if mode == "missing-ui" else [agent]
        if mode == "ambiguous-ui":
            agents.append(dict(agent, pane_id="pane-2"))
        print(json.dumps({"context": {"backend": "herdr", "instance": os.environ["HERDR_SOCKET_PATH"]},
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
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        (self.repo / "file").write_text("base")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")
        self.record = self.repo / ".git/dispatch-workers/APP-TEST/worker.json"
        self.label = self.root / "label"
        self.label.write_text("dispatch-app-test")
        self.tab_id = "tab-1"
        self.startup_panes = []
        self.startup_tabs = []
        (self.root / "original tasks.db").write_text("existing database")
        self.ui_calls = []
        self.socket_dir = tempfile.TemporaryDirectory(prefix="dsp-ui-")
        self.addCleanup(self.socket_dir.cleanup)
        endpoint = str(Path(self.socket_dir.name) / "api")
        self.env["HERDR_SOCKET_PATH"] = endpoint
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(endpoint)
        server.listen()
        server.settimeout(0.1)
        stopped = threading.Event()

        def serve():
            while not stopped.is_set():
                try:
                    stream, _ = server.accept()
                except TimeoutError:
                    continue
                with stream, stream.makefile("rb") as incoming:
                    line = incoming.readline()
                    if not line:  # Read-only socket probes send no request.
                        continue
                    request = json.loads(line)
                    self.ui_calls.append(request)
                    if request["method"] == "session.snapshot":
                        result = {
                            "snapshot": {
                                "version": "0.9.0",
                                "protocol": 22,
                                "panes": [
                                    {
                                        "pane_id": "native-1",
                                        "terminal_id": "terminal-1",
                                        "tab_id": self.tab_id,
                                        "workspace_id": "ws-1",
                                    }
                                ]
                                + self.startup_panes,
                                "tabs": [
                                    {
                                        "tab_id": self.tab_id,
                                        "workspace_id": "ws-1",
                                        "label": self.label.read_text(),
                                    }
                                ]
                                + self.startup_tabs,
                            }
                        }
                    elif request["method"] == "pane.process_info":
                        result = {
                            "process_info": {
                                "shell_pid": os.getpid()
                                if request["params"]["pane_id"] == "native-1"
                                else 999999
                            }
                        }
                    elif request["method"] == "layout.apply":
                        self.startup_panes.append(
                            dict(
                                pane_id="aven-pane",
                                terminal_id="aven-terminal",
                                tab_id="aven-tab",
                                workspace_id="ws-1",
                            )
                        )
                        self.startup_tabs.append(
                            dict(tab_id="aven-tab", workspace_id="ws-1", label="aven")
                        )
                        result = {"tab": {"tab_id": "aven-tab"}}
                    elif request["method"] == "tab.close":
                        tab = request["params"]["tab_id"]
                        self.startup_panes = [
                            p for p in self.startup_panes if p["tab_id"] != tab
                        ]
                        self.startup_tabs = [
                            t for t in self.startup_tabs if t["tab_id"] != tab
                        ]
                        result = {}
                    else:
                        self.label.write_text(request["params"]["label"])
                        result = {}
                    stream.sendall(
                        json.dumps({"id": request["id"], "result": result}).encode()
                        + b"\n"
                    )

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()

        def stop():
            stopped.set()
            thread.join(timeout=2)
            server.close()

        self.addCleanup(stop)

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

    def prepare_run(self):
        path = self.repo / ".git/dispatch-ui/APP-TEST.json"
        if not path.exists():
            mode = self.env["MODE"]
            self.env["MODE"] = ""
            try:
                self.cli("startup", "APP-TEST")
            finally:
                self.env["MODE"] = mode

    def launch(self, *extra, ok=True):
        self.prepare_run()
        return self.cli(
            "launch",
            "APP-TEST",
            "--base",
            "main",
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

    def test_startup_from_subdirectory_uses_defaults_and_reuses_tab(self):
        subdir = self.repo / "nested"
        subdir.mkdir()
        results = []
        for cwd in (subdir, self.repo):
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "dispatch.py"), "startup", "APP-TEST"],
                cwd=cwd,
                env=self.env,
                text=True,
                capture_output=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            results.append(json.loads(result.stdout))
        self.assertEqual(results[0]["aven_tab"], results[1]["aven_tab"])
        self.assertEqual(
            results[0]["routing"],
            dict(
                db=str(self.root / "original tasks.db"),
                workspace="default",
                project="project",
            ),
        )
        creates = [
            call["params"] for call in self.ui_calls if call["method"] == "layout.apply"
        ]
        self.assertEqual(len(creates), 1)
        self.assertEqual(creates[0]["root"]["cwd"], str(self.repo))
        self.assertEqual(
            creates[0]["root"]["command"][1:], ["tui", "--project", "project"]
        )
        self.assertIn(["aven", "context", "APP-TEST", "--json"], self.calls())
        self.assertEqual(
            len([c for c in self.calls() if c[:2] == ["aven", "doctor"]]), 1
        )
        self.assertFalse((self.repo / ".aven").exists())
        self.assertEqual(self.adds(), [])
        self.assertEqual(self.label.read_text(), "dispatcher")

    def test_close_run_requires_authorization_and_preserves_dispatcher(self):
        startup = self.cli("startup", "APP-TEST", "--run-id", "completed-run")
        self.cli("close-run", "APP-TEST", "--run-id", "completed-run", ok=False)
        self.assertEqual(len(self.startup_panes), 1)
        self.env["WRITE_SUMMARY"] = "1"
        for _ in range(2):
            result = self.cli(
                "close-run",
                "APP-TEST",
                "--run-id",
                "completed-run",
                "--authorize-close",
            )
            self.assertTrue(result["aven_closed"])
        self.assertEqual(self.startup_panes, [])
        self.assertEqual(self.startup_tabs, [])
        self.assertEqual(self.label.read_text(), "dispatcher")
        self.assertEqual(sum(c["method"] == "tab.close" for c in self.ui_calls), 1)
        saved = json.loads(Path(startup["record_path"]).read_text())
        self.assertTrue(saved["aven_closed"])
        result = self.cli("startup", "APP-TEST", "--run-id", "completed-run", ok=False)
        self.assertIn("closure has started", result["error"])

    def test_startup_missing_aven_has_clear_diagnostic_without_ui_changes(self):
        (self.root / "bin/aven").unlink()
        self.env["PATH"] = str(self.root / "bin")
        result = self.cli("startup", "APP-TEST", ok=False)
        self.assertIn("aven is missing from PATH", result["error"])
        self.assertEqual(self.ui_calls, [])
        self.assertEqual(self.calls(), [])

    def test_startup_missing_database_or_ui_never_creates_tab(self):
        (self.root / "original tasks.db").unlink()
        self.cli("startup", "APP-TEST", ok=False)
        self.assertEqual(self.ui_calls, [])
        (self.root / "original tasks.db").write_text("existing")
        self.env.pop("HERDR_ENV")
        self.env.pop("TMUX", None)
        result = self.cli("startup", "APP-TEST", ok=False)
        self.assertIn("original Herdr or tmux", result["error"])
        self.assertEqual(self.ui_calls, [])

    def test_worker_is_created_with_task_reference_as_tab_name(self):
        data = self.launch()
        self.assertEqual((self.root / "created-label").read_text(), "APP-TEST")
        self.assertEqual(data["handle"], "dispatch-app-test")
        self.assertEqual(data["worker_tab"]["tab_id"], "tab-1")
        self.assertEqual(self.label.read_text(), "APP-TEST")

    def test_literal_prompt_default_routing_and_saved_identity(self):
        data = self.launch()
        saved = json.loads(self.record.read_text())
        self.assertEqual(saved, data)
        self.assertEqual(data["launch_base"], self.base)
        self.assertEqual(data["repo"], str(self.repo))
        self.assertEqual(data["agent_type"], "pi")
        self.assertEqual(data["container"]["id"], "container-1")
        self.assertEqual(data["worker_worktree"], "/guest/worker")
        self.assertEqual(data["ui"]["agents"][0]["pane_id"], "boot~terminal-1")
        self.assertEqual(data["routing"], {})
        self.assertEqual(self.calls()[0], ["aven", "doctor", "--json"])
        prompt = Path(data["prompt"]).read_text()
        self.assertIn("$(touch SENTINEL)", prompt)
        self.assertIn("`backticks`", prompt)
        self.assertIn("Keep this durable context", prompt)
        self.assertTrue(prompt.startswith("## Work location\n"))
        self.assertNotIn("## Write scope", prompt)
        self.assertNotIn("## Aven reporting", prompt)
        self.assertIn("APP-TEST: Literal", prompt)
        self.assertEqual(
            [call for call in self.calls() if call[:2] == ["aven", "context"]],
            [
                ["aven", "context", "APP-TEST", "--json"],  # startup
                ["aven", "context", "APP-TEST", "--json"],  # assignment
                ["aven", "context", "APP-TEST"],
                ["aven", "context", "APP-TEST", "--json"],  # activation
            ],
        )
        self.assertNotIn("task_context", saved)
        self.assertEqual(saved["prior_note_ids"], ["launch-note"])
        self.assertNotIn("```text", prompt)
        self.assertNotIn('"task_context":', prompt)
        self.assertNotIn('"task_ref":', prompt)
        self.assertIn("Launch-base commit: " + self.base, prompt)
        self.assertFalse((self.repo / "SENTINEL").exists())
        self.assertTrue(Path(data["prompts"][0]["archive_path"]).exists())
        self.assertFalse(Path(data["prompt"]).is_relative_to(self.root / "worker"))
        self.assertIn("--sandbox", self.adds()[0])
        self.assertIn("agents.linux.yaml", data["config"])

    def test_created_tab_name_and_resume_preserve_identity(self):
        data = self.launch()
        self.assertEqual(self.label.read_text(), "APP-TEST")
        self.assertEqual(data["handle"], "dispatch-app-test")
        self.assertEqual(data["branch"], "dispatch/app-test")
        self.assertEqual(data["worker_tab"]["tab_id"], "tab-1")
        self.label.write_text("✅ dispatch-app-test")
        before = self.record.read_bytes()
        self.cli("inspect", "APP-TEST")
        self.assertEqual(self.record.read_bytes(), before)
        self.assertEqual(self.label.read_text(), "✅ dispatch-app-test")
        resumed = self.cli("inspect", "APP-TEST", "--resume")
        self.assertEqual(self.label.read_text(), "✅ dispatch-app-test")
        self.assertEqual(resumed["worker_tab"], data["worker_tab"])
        self.assertEqual(len(self.adds()), 1)

    def test_displayed_case_and_waiting_state_are_preserved(self):
        self.env.update(DISPLAY_REF="APP-TeST", MODE="waiting")
        self.record = self.record.parent.parent / "APP-TeST/worker.json"
        data = self.launch()
        self.assertEqual(data["task_ref"], "APP-TeST")
        self.assertEqual(self.label.read_text(), "APP-TeST")
        self.assertEqual(data["handle"], "dispatch-app-test")
        self.assertEqual(data["branch"], "dispatch/app-test")
        self.label.write_text("💬 APP-TeST")
        self.cli("inspect", "APP-TeST", "--resume")
        self.assertEqual(self.label.read_text(), "💬 APP-TeST")
        self.assertEqual(len(self.adds()), 1)

    def test_resume_rejects_moved_tab_even_with_correct_label(self):
        self.launch()
        self.ui_calls.clear()
        self.tab_id = "unrelated"
        data = self.cli("inspect", "APP-TEST", "--resume", ok=False)
        self.assertIn("identity changed", data["error"])
        self.assertFalse(any(call["method"] == "tab.rename" for call in self.ui_calls))
        self.assertEqual(len(self.adds()), 1)
        saved = json.loads(self.record.read_text())
        self.assertEqual(saved["worker_tab"]["tab_id"], "tab-1")

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
        self.assertEqual(self.label.read_text(), "APP-TEST")
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
        self.assertEqual(data["ui"]["agents"][0]["pane_id"], "boot~terminal-1")
        self.assertEqual(
            data["events"][-1]["ui"]["agents"][0]["pane_id"], "boot~CHANGED"
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

    def test_missing_default_config_is_managed(self):
        config = self.root / ".config/workmux/agents.linux.yaml"
        config.unlink()
        data = self.launch()
        self.assertEqual(data["platform"], "linux")
        self.assertEqual(config.read_text(), "agent: pi\nsandbox:\n  enabled: true\n")
        self.assertEqual(len(self.adds()), 1)

    def test_platform_override_on_resume_is_rejected(self):
        self.launch()
        data = self.cli("launch", "APP-TEST", "--platform", "darwin", ok=False)
        self.assertIn("saved platform", data["error"])
        self.assertEqual(len(self.adds()), 1)

    @unittest.skipIf(sys.platform == "darwin", "Requires a non-macOS host")
    def test_darwin_requires_macos_host(self):
        data = self.launch("--platform", "darwin", ok=False)
        self.assertIn("macOS host", data["error"])
        self.assertEqual(self.adds(), [])

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

    def test_local_runtime_launches_without_approval_flag(self):
        config = self.root / "local.yaml"
        config.write_text("agent: pi\nsandbox:\n  enabled: false\n")
        data = self.launch("--runtime", "local", "--config", str(config))
        self.assertIsNone(data["container"])
        self.assertEqual(data["worker_worktree"], str(self.root / "worker"))
        self.assertNotIn("--sandbox", self.adds()[0])

    def test_config_filename_does_not_gate_launch(self):
        config = self.root / "agents.macos.yaml"
        config.write_text("agent: pi\nsandbox:\n  enabled: true\n")
        self.launch("--config", str(config))
        self.assertEqual(len(self.adds()), 1)

    def test_launch_requires_confirmed_open_run(self):
        data = self.cli(
            "launch", "APP-TEST", "--base", "main", "--check", '["true"]', ok=False
        )
        self.assertIn("Run startup first", data["error"])
        self.assertEqual(self.adds(), [])
        self.assertFalse(self.record.exists())
        self.prepare_run()
        path = self.repo / ".git/dispatch-ui/APP-TEST.json"
        saved = json.loads(path.read_text())
        saved["ok"] = False
        path.write_text(json.dumps(saved))
        data = self.launch(ok=False)
        self.assertIn("startup is not confirmed", data["error"])
        self.assertEqual(self.adds(), [])
        saved.update(ok=True, aven_close_attempted=True)
        path.write_text(json.dumps(saved))
        data = self.launch(ok=False)
        self.assertIn("closure has started", data["error"])
        self.assertEqual(self.adds(), [])

    def test_active_transition_is_automatic_and_read_back(self):
        self.env["AVEN_INITIAL_STATUS"] = "todo"
        data = self.launch()
        self.assertTrue(data["launch_confirmed"])
        self.assertTrue(data["events"][-1]["activation"]["ok"])
        self.assertEqual(data["events"][-1]["activation"]["status"], "active")
        self.cli("inspect", "APP-TEST", "--resume")
        edits = [c for c in self.calls() if c[:2] == ["aven", "edit"]]
        self.assertEqual(edits, [["aven", "edit", "APP-TEST", "--status", "active"]])
        self.assertEqual(len(self.adds()), 1)

    def test_active_write_failures_resume_without_relaunch(self):
        for mode in (
            "active-write-fails",
            "active-readback-fails",
            "active-lost-response",
        ):
            with self.subTest(mode=mode):
                self.env.update(AVEN_INITIAL_STATUS="todo", MODE=mode)
                # Reuse the one worker across failures. Live status, not the
                # previous event receipt, determines whether to write again.
                (self.root / "aven-status").unlink(missing_ok=True)
                data = self.launch(ok=False)
                self.assertTrue(data["launch_confirmed"])
                self.assertNotIn("ok", data["events"][-1]["activation"])
                self.env["MODE"] = ""
                self.cli("inspect", "APP-TEST", "--resume")
                self.assertEqual(len(self.adds()), 1)
                if mode == "active-lost-response":
                    edits = [c for c in self.calls() if c[:2] == ["aven", "edit"]]
                    self.assertEqual(len(edits), 5)  # two repairs, one lost response

    def test_close_run_rejects_unfinished_and_missing_worker_evidence(self):
        self.launch()
        data = self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("unfinished or has pending cleanup", data["error"])
        self.assertEqual(len(self.startup_tabs), 1)
        self.record.rename(self.record.with_suffix(".retained"))
        self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertFalse(any(c["method"] == "tab.close" for c in self.ui_calls))

    def completed_record(self):
        """Saved completion seam; resources are already absent."""
        self.prepare_run()
        self.record.parent.mkdir(parents=True)
        saved = dict(
            schema_version=1,
            run_id="APP-TEST",
            task_ref="APP-TEST",
            task_id="task-id",
            repo=str(self.repo),
            common_dir=str(self.repo / ".git"),
            worktree=str(self.root / "removed-worker"),
            branch="dispatch/app-test",
            base="main",
            integration={"verified_base_sha": self.base},
            finish=dict(
                ok=True,
                task_complete=True,
                cleanup_complete=True,
                pending_cleanup=[],
                housekeeping=[],
            ),
        )
        self.record.write_text(json.dumps(saved))
        return saved

    def test_close_run_checks_live_done_and_resource_absence(self):
        saved = self.completed_record()
        data = self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("not confirmed done", data["error"])
        self.env["AVEN_INITIAL_STATUS"] = "done"
        self.git("branch", saved["branch"])
        data = self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("resource reappeared", data["error"])
        self.git("branch", "-d", saved["branch"])
        data = self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("No matching report", data["error"])
        self.env["WRITE_SUMMARY"] = "1"
        result = self.cli("close-run", "APP-TEST", "--authorize-close")
        self.assertEqual(result["worker_reconciliation"][0]["task_ref"], "APP-TEST")
        self.assertTrue(result["aven_closed"])

    def test_close_run_blocks_done_with_pending_cleanup(self):
        saved = self.completed_record()
        self.env["AVEN_INITIAL_STATUS"] = "done"
        saved["finish"]["pending_cleanup"] = [{"identity": "retained"}]
        self.record.write_text(json.dumps(saved))
        data = self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("pending cleanup", data["error"])
        self.assertFalse(any(c["method"] == "tab.close" for c in self.ui_calls))

    def test_close_run_rejects_lost_base_delivery(self):
        saved = self.completed_record()
        self.env["AVEN_INITIAL_STATUS"] = "done"
        tree = self.git("rev-parse", "HEAD^{tree}")
        other = self.git("commit-tree", tree, "-m", "unrelated verified base")
        saved["integration"]["verified_base_sha"] = other
        self.record.write_text(json.dumps(saved))
        self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertFalse(any(c["method"] == "tab.close" for c in self.ui_calls))

    def test_close_run_rejects_summary_from_before_startup(self):
        self.env["WRITE_SUMMARY"] = "1"
        self.prepare_run()
        data = self.cli("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("SUMMARY predates", data["error"])
        self.assertFalse(any(c["method"] == "tab.close" for c in self.ui_calls))

    def test_explicit_run_id_is_saved_and_reused_on_resume(self):
        self.cli("startup", "APP-TEST", "--run-id", "shared-run")
        data = self.cli(
            "launch",
            "APP-TEST",
            "--run-id",
            "shared-run",
            "--base",
            "main",
            "--check",
            '["true"]',
        )
        self.assertEqual(data["run_id"], "shared-run")
        index = json.loads(Path(data["run_record_path"]).read_text())
        self.assertEqual(index["worker_refs"], ["APP-TEST"])
        resumed = self.cli("inspect", "APP-TEST", "--resume")
        self.assertEqual(resumed["run_id"], "shared-run")
        self.assertEqual(len(self.adds()), 1)

    def test_run_override_cannot_move_existing_worker_to_another_run(self):
        self.launch()
        original = self.repo / ".git/dispatch-ui/APP-TEST.json"
        other = original.with_name("another-run.json")
        other.write_bytes(original.read_bytes())
        data = self.cli("launch", "APP-TEST", "--run-id", "another-run", ok=False)
        self.assertIn("Run override differs", data["error"])
        self.assertEqual(len(self.adds()), 1)

    def test_invalid_check_rejected_before_creation(self):
        self.prepare_run()
        for argv in (["echo", "bad\0argument"], ["", "argument"], ["echo", 1]):
            with self.subTest(argv=argv):
                self.cli(
                    "launch",
                    "APP-TEST",
                    "--base",
                    "main",
                    "--check",
                    json.dumps(argv),
                    ok=False,
                )
        self.assertEqual(self.adds(), [])
        self.assertFalse(self.record.exists())

    def test_empty_check_argument_is_preserved(self):
        self.prepare_run()
        data = self.cli(
            "launch", "APP-TEST", "--base", "main", "--check", '["printf", ""]'
        )
        self.assertEqual(data["acceptance_checks"], [["printf", ""]])

    def test_git_environment_cannot_redirect_external_tools(self):
        self.prepare_run()
        self.env["GIT_DIR"] = str(self.root / "missing-git-directory")
        self.env["GIT_WORK_TREE"] = str(self.root / "wrong-worktree")
        self.launch()
        self.assertEqual(len(self.adds()), 1)

    def test_serialization_blocks_creation(self):
        with (self.repo / ".git/dispatch.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            self.cli("launch", "APP-TEST", ok=False)
        self.assertEqual(self.calls(), [])

    def test_existing_branch_without_record_blocks_creation(self):
        self.git("branch", "dispatch/app-test")
        self.launch(ok=False)
        self.assertEqual(self.adds(), [])

    def test_resume_uses_defaults_instead_of_legacy_routing(self):
        data = self.launch()
        self.assertEqual(data["routing"], {})
        saved = json.loads(self.record.read_text())
        saved["routing"] = {"workspace": "explicit", "db": "/explicit tasks.db"}
        self.record.write_text(json.dumps(saved))
        prompt = Path(data["prompt"]).read_text()
        self.assertNotIn("## Aven reporting", prompt)
        self.assertIn(["aven", "context", "APP-TEST"], self.calls())

        self.cli("inspect", "APP-TEST", "--resume")
        self.assertEqual(len(self.adds()), 1)
        self.assertEqual(
            [call for call in self.calls() if call[0] == "aven"][-1],
            ["aven", "context", "APP-TEST", "--json"],
        )

    def test_human_context_failure_does_not_launch_or_save_record(self):
        self.env["MODE"] = "human-context-error"
        data = self.launch(ok=False)
        self.assertIn("cannot read human context", data["error"])
        self.assertEqual(self.adds(), [])
        self.assertFalse(self.record.exists())

    def test_context_failure_does_not_launch_or_save_record(self):
        self.env["MODE"] = "context-error"
        data = self.launch(ok=False)
        self.assertIn("cannot read task context", data["error"])
        self.assertEqual(self.adds(), [])
        self.assertFalse(self.record.exists())

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
