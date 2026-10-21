"""Finish CLI contracts with real Git and controlled external runtime responses."""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import threading
import unittest
from pathlib import Path

import test_safety as safety

FINISH_AVEN_CLI = r"""
import argparse, json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as out:
    out.write(json.dumps(["aven", *args]) + "\n")
path = Path(os.environ["FINISH_AVEN_STATE"])
state = json.loads(path.read_text())
mode = os.environ.get("FINISH_AVEN_MODE")
if args[0] == "note":
    state["notes"].append(Path(args[args.index("--file") + 1]).read_text())
elif args[0] == "edit":
    parser = argparse.ArgumentParser()
    parser.add_argument("task_ref")
    parser.add_argument("--status", choices=["done"], required=True)

    parser.parse_args(args[1:])
    if mode == "status-error":
        sys.stderr.write("status store unavailable")
        sys.exit(7)
    if mode != "status-noop":
        state["status"] = "done"
elif args[0] == "context":
    if mode == "read-error":
        sys.stderr.write("status read unavailable")
        sys.exit(8)
else:
    sys.exit(9)
path.write_text(json.dumps(state))
if args[0] == "edit" and mode == "interrupted-write":
    sys.stderr.write("connection lost after write")
    sys.exit(7)
print(json.dumps({"task": {"display_ref": "SKL-TEST", "status": state["status"]}}))
"""


class FinishTests(unittest.TestCase):
    git = safety.SafetyTests.git

    def setUp(self):
        safety.SafetyTests.setUp(self)
        self.env["CLI_MODE"] = "exited"
        self.aven_state = self.root / "aven-state.json"
        self.aven_state.write_text(json.dumps({"status": "active", "notes": []}))
        self.env["FINISH_AVEN_STATE"] = str(self.aven_state)
        binary = self.root / "bin/aven"
        binary.write_text("#!" + sys.executable + "\n" + FINISH_AVEN_CLI)
        self.path = self.repo / ".git/dispatch-workers/SKL-TEST/worker.json"
        self.path.parent.mkdir(parents=True)
        self.verification = self.path.parent / "base.json"
        self.verification.write_text(
            json.dumps(
                {
                    "ok": True,
                    "tested_sha": self.base,
                    "worker_sha": self.base,
                    "base_ref": "refs/heads/main",
                    "repo": {
                        "common_dir": str(self.repo / ".git"),
                        "worktree": str(self.repo),
                    },
                    "checks": [{"argv": ["true"], "status": "passed", "returncode": 0}],
                    "worker_is_ancestor": True,
                    "base_moved": False,
                }
            )
        )
        self.record = {
            "schema_version": 1,
            "task_ref": "SKL-TEST",
            "repo": str(self.repo),
            "common_dir": str(self.repo / ".git"),
            "worktree": str(self.worker),
            "branch": "worker",
            "base": "main",
            "handle": "worker",
            "runtime": "docker",
            "worker_worktree": "/worker",
            "container": {"id": "container-1"},
            "prompts": [],
            "routing": {},
            "acceptance_checks": [["true"]],
            "events": [],
            "ui": {"context": {"backend": "herdr"}, "agents": [{"pane_id": "pane-1"}]},
            "integration": {
                "ok": True,
                "integrated_worker_sha": self.base,
                "verified_base_sha": self.base,
                "verification_evidence": str(self.verification),
            },
        }
        self.store()

    def store(self):
        self.path.write_text(json.dumps(self.record))

    def cli(self, *args, ok=True):
        result = subprocess.run(
            [
                sys.executable,
                str(safety.SCRIPTS / "finish_worker.py"),
                "SKL-TEST",
                *args,
            ],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stdout + result.stderr
        )
        return json.loads(result.stdout)

    def herdr_finish(self, lose_response=False):
        # Real Git + finish CLI + real local Unix transport. This is a protocol
        # fixture, not a substitute for the host Workmux/Herdr acceptance check.
        endpoint = str(self.root / "herdr.sock")
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.addCleanup(server.close)
        server.bind(endpoint)
        server.listen()
        server.settimeout(0.1)
        stat = os.stat(endpoint)
        pid = os.getpid()
        start = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
        boot_id = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        boot = f"{stat.st_dev}-{stat.st_ino}-{pid}-{start}-{boot_id}"
        self.record["ui"] = {
            "context": {"backend": "herdr", "instance": endpoint},
            "agents": [{"pane_id": boot + "~worker-terminal"}],
        }
        self.prompt()
        (self.repo / ".git/info/exclude").write_text(".workmux/\n")
        self.store()
        closed = []
        errors = []
        done = threading.Event()

        def serve():
            try:
                while not done.is_set():
                    try:
                        stream, _ = server.accept()
                    except socket.timeout:
                        continue
                    with stream:
                        with stream.makefile("rb") as reader:
                            request = json.loads(reader.readline())
                        method = request["method"]
                        if method == "tab.close":
                            self.assertEqual(
                                request["params"], {"tab_id": "worker-tab"}
                            )
                            closed.append("worker-tab")
                            if lose_response:
                                continue
                            result = {}
                        else:
                            self.assertEqual(method, "session.snapshot")
                            panes = [
                                {
                                    "pane_id": "foreign",
                                    "terminal_id": "foreign",
                                    "workspace_id": "ws",
                                    "tab_id": "unrelated",
                                    "cwd": str(self.repo),
                                }
                            ]
                            tabs = [{"tab_id": "unrelated", "workspace_id": "ws"}]
                            if not closed:
                                panes.append(
                                    {
                                        "pane_id": "worker-pane",
                                        "terminal_id": "worker-terminal",
                                        "workspace_id": "ws",
                                        "tab_id": "worker-tab",
                                        "cwd": str(self.worker),
                                    }
                                )
                                tabs.append(
                                    {"tab_id": "worker-tab", "workspace_id": "ws"}
                                )
                            result = {
                                "snapshot": {
                                    "version": "0.9.0",
                                    "protocol": 22,
                                    "panes": panes,
                                    "tabs": tabs,
                                }
                            }
                        stream.sendall(
                            json.dumps({"id": request["id"], "result": result}).encode()
                            + b"\n"
                        )
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        try:
            first = self.cli()
            self.assertFalse(self.worker.exists())
            self.assertNotIn(str(self.worker), self.git(self.repo, "worktree", "list"))
            if lose_response:
                self.assertFalse(first["cleanup_complete"])
                self.assertEqual(first["housekeeping"][0]["status"], "pending")
                self.assertTrue(first["housekeeping"][0]["evidence"])
            else:
                self.assertTrue(first["finish_complete"])
            self.record = json.loads(self.path.read_text())
            self.reverify_base()
            retried = self.cli()
            self.assertEqual(retried["plan"], first["plan"])
            self.assertTrue(retried["cleanup_complete"])
            self.assertTrue(retried["finish_complete"])
            self.assertEqual(retried["housekeeping"][0]["status"], "closed")
            self.assertEqual(closed, ["worker-tab"])
            self.assertEqual(errors, [])
        finally:
            done.set()
            thread.join(timeout=5)

    @unittest.skipUnless(sys.platform == "linux", "Linux saved peer lifetime fixture")
    def test_finish_removes_git_worktree_and_closes_exact_herdr_tab(self):
        self.herdr_finish()

    @unittest.skipUnless(sys.platform == "linux", "Linux saved peer lifetime fixture")
    def test_finish_reconciles_lost_herdr_close_after_worktree_removal(self):
        self.herdr_finish(lose_response=True)

    def test_finish_executes_without_separate_authorization(self):
        before = self.path.read_bytes()
        inspected = self.cli("--inspect")
        self.assertTrue(inspected["ok"])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertTrue(self.worker.exists())
        result = self.cli()
        self.assertTrue(result["delivered"])
        self.assertTrue(result["task_complete"])
        self.assertFalse(self.worker.exists())
        self.assertEqual(result["pending_cleanup"], [])
        self.cli()
        self.assertFalse(self.worker.exists())
        self.assertTrue((self.path.parent / "completion.md").exists())
        state = json.loads(self.aven_state.read_text())
        self.assertEqual(state["status"], "done")
        self.assertTrue(any("VERIFIED:" in note for note in state["notes"]))

    def test_completion_uses_defaults_despite_legacy_routing_after_report(self):
        self.record["routing"] = {"db": "/saved/tasks.db", "workspace": "saved"}
        self.record["agent_type"] = "pi"
        self.store()
        result = self.cli()
        self.assertTrue(result["task_complete"])
        calls = [
            json.loads(line)
            for line in Path(self.env["CALL_LOG"]).read_text().splitlines()
        ]
        aven = [call for call in calls if call[0] == "aven"]
        self.assertEqual(
            [call[1] for call in aven], ["note", "context", "edit", "context"]
        )
        self.assertEqual(
            aven[-2],
            [
                "aven",
                "edit",
                "SKL-TEST",
                "--status",
                "done",
            ],
        )
        self.assertEqual(json.loads(self.path.read_text())["agent_type"], "pi")

    def prompt(self, name="PROMPT-one.md", text="generated"):
        directory = self.worker / ".workmux"
        directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_text(text)
        entry = {
            "path": ".workmux/" + name,
            "sha256": hashlib.sha256(text.encode()).hexdigest(),
        }
        self.record["prompts"].append(entry)
        self.store()
        return path

    def test_unknown_exit_blocks_task_completion(self):
        self.env["CLI_MODE"] = "missing"
        result = self.cli(ok=False)
        self.assertFalse(result["delivered"])
        self.assertFalse(result["task_complete"])
        self.assertTrue(self.worker.exists())
        self.assertNotIn("aven", Path(self.env["CALL_LOG"]).read_text())

    def test_changed_prompt_is_pending_after_task_completion(self):
        path = self.prompt()
        path.write_text("changed")
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertEqual(path.read_text(), "changed")
        self.assertEqual(result["pending_cleanup"][0]["identity"], str(self.worker))
        self.assertEqual(result["pending_cleanup"][0]["owner"], "dispatcher")
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "done")
        self.assertTrue(result["pending_cleanup"][0]["next_action"])
        self.assertTrue(Path(result["pending_cleanup"][0]["evidence"]).exists())

    def test_dirty_and_unknown_files_remain_pending(self):
        (self.worker / "file").write_text("dirty")
        (self.worker / "unknown").write_text("retain")
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertTrue(result["pending_cleanup"])
        self.assertFalse(result["cleanup_complete"])
        self.assertFalse(result["finish_complete"])
        self.assertIn("PENDING", Path(result["completion_report"]).read_text())
        self.assertTrue((self.worker / "unknown").exists())

    def pending_finish(self):
        prompt = self.prompt()
        prompt.write_text("changed")
        first = self.cli()
        self.assertTrue(first["task_complete"])
        self.assertTrue(first["pending_cleanup"])
        self.record = json.loads(self.path.read_text())
        return prompt, first

    def reverify_base(self, message="advance base"):
        self.git(self.repo, "commit", "--allow-empty", "-qm", message)
        sha = self.git(self.repo, "rev-parse", "HEAD")
        self.record["integration"]["verified_base_sha"] = sha
        data = json.loads(self.verification.read_text())
        data["tested_sha"] = sha
        self.verification.write_text(json.dumps(data))
        self.store()
        return sha

    def assert_cleanup_blocked(self, prompt):
        result = self.cli(ok=False)
        self.assertTrue(result["task_complete"])
        self.assertTrue(result["delivered"])
        self.assertFalse(result["finish_complete"])
        self.assertFalse(result["cleanup_complete"])
        self.assertTrue(prompt.exists())
        self.assertTrue(self.worker.exists())
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "done")
        return result

    def test_pending_cleanup_needs_no_reverification_after_base_advance(self):
        prompt, first = self.pending_finish()
        self.git(self.repo, "commit", "--allow-empty", "-qm", "task B")
        self.verification.unlink()
        before = self.path.read_bytes()
        self.cli("--inspect")
        self.assertEqual(self.path.read_bytes(), before)
        prompt.write_text("generated")
        result = self.cli()
        self.assertEqual(result["pending_cleanup"], [])
        self.assertFalse(self.worker.exists())
        self.assertEqual(result["plan"], first["plan"])
        self.cli()
        self.assertEqual(len([c for c in self.aven_mutations() if c[1] == "edit"]), 1)

    def test_retry_ignores_missing_verification_and_changed_acceptance_checks(self):
        prompt, _ = self.pending_finish()
        self.git(self.repo, "commit", "--allow-empty", "-qm", "task B")
        self.verification.unlink()
        self.record["acceptance_checks"] = [["false"]]
        self.record["routing"] = {"changed": True}
        self.store()
        prompt.write_text("generated")
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertEqual(result["pending_cleanup"], [])

    def test_reverified_retry_rejects_changed_resource_or_assignment(self):
        prompt, _ = self.pending_finish()
        self.reverify_base()
        original = json.dumps(self.record)
        for key, value in (
            ("container", {"id": "replacement"}),
            ("ui", {"context": {"backend": "tmux"}, "agents": []}),
            ("prompts", []),
            ("cleanup_parent", str(self.root)),
            ("worker_worktree", "/replacement"),
            ("handle", "replacement"),
        ):
            with self.subTest(key=key):
                self.record = json.loads(original)
                self.record[key] = value
                self.store()
                self.assertIn("changed", self.assert_cleanup_blocked(prompt)["error"])
        self.record = json.loads(original)
        self.store()

    def test_reverified_retry_rejects_changed_worker(self):
        prompt, _ = self.pending_finish()
        sha = self.reverify_base()
        self.git(self.worker, "reset", "--hard", sha)
        self.record["integration"]["integrated_worker_sha"] = sha
        data = json.loads(self.verification.read_text())
        data["worker_sha"] = sha
        self.verification.write_text(json.dumps(data))
        self.store()
        self.assertIn("plan changed", self.assert_cleanup_blocked(prompt)["error"])

    def test_cleanup_does_not_reopen_base_ancestry_acceptance(self):
        prompt, _ = self.pending_finish()
        self.reverify_base()
        self.cli()
        self.record = json.loads(self.path.read_text())
        self.git(self.repo, "reset", "--hard", self.base)
        self.reverify_base("sibling base")
        prompt.write_text("generated")
        self.assertEqual(self.cli()["pending_cleanup"], [])

    def test_reverified_retry_unknown_exit_preserves_done_delivery(self):
        prompt, _ = self.pending_finish()
        self.reverify_base()
        self.env["CLI_MODE"] = "wrong-id"
        result = self.assert_cleanup_blocked(prompt)
        self.assertIn("exit is uncertain", result["error"])
        self.assertNotIn("base_verifications", result)

    def test_reverified_retry_rejects_resource_reappearance(self):
        self.cli()
        self.record = json.loads(self.path.read_text())
        self.reverify_base()
        self.git(
            self.repo, "worktree", "add", "-b", "worker", str(self.worker), self.base
        )
        prompt = self.worker / "evidence"
        prompt.write_text("retain replacement")
        self.assertIn("reappeared", self.assert_cleanup_blocked(prompt)["error"])

    def test_reverified_retry_rejects_archived_prompt_reappearance(self):
        prompt = self.prompt()
        (self.worker / "unknown").write_text("retain")
        self.cli()
        self.assertFalse(prompt.exists())
        self.record = json.loads(self.path.read_text())
        self.reverify_base()
        prompt.parent.mkdir(exist_ok=True)
        prompt.write_text("generated")
        self.assertIn("reappeared", self.assert_cleanup_blocked(prompt)["error"])

    def test_reverified_retry_rejects_branch_reappearance(self):
        self.cli()
        self.record = json.loads(self.path.read_text())
        self.reverify_base()
        self.git(self.repo, "branch", "worker", self.base)
        result = self.cli(ok=False)
        self.assertIn("reappeared", result["error"])
        self.assertTrue(result["task_complete"])
        self.assertEqual(self.git(self.repo, "rev-parse", "worker"), self.base)

    def test_blocked_retry_does_not_manufacture_task_completion(self):
        self.env["CLI_MODE"] = "wrong-id"
        self.cli(ok=False)
        self.record = json.loads(self.path.read_text())
        self.reverify_base()
        result = self.cli(ok=False)
        self.assertFalse(result["task_complete"])
        self.assertFalse(result["delivered"])
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "active")

    def test_base_moved_does_not_block_cleanup_or_completion(self):
        self.git(self.repo, "commit", "--allow-empty", "-qm", "base moved")
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertFalse(self.worker.exists())

    def test_wrong_container_identity_blocks_completion(self):
        self.env["CLI_MODE"] = "wrong-id"
        result = self.cli(ok=False)
        self.assertFalse(result["task_complete"])
        self.assertTrue(self.worker.exists())

    def test_partial_archive_resumes_without_recreating_sources(self):
        path = self.prompt()
        (self.worker / "unknown").write_text("retain")
        first = self.cli()
        self.assertTrue(first["pending_cleanup"])
        self.assertFalse(path.exists())
        (self.worker / "unknown").unlink()
        second = self.cli()
        self.assertTrue(second["task_complete"])
        self.assertFalse(self.worker.exists())

    def test_partial_worktree_removal_resumes_branch_only(self):
        self.cli()
        self.git(self.repo, "branch", "worker", self.base)
        record = json.loads(self.path.read_text())
        record["finish"]["actions"]["branch"] = "attempted"
        record["finish"]["task_complete"] = False
        self.path.write_text(json.dumps(record))
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertFalse(self.worker.exists())
        self.assertEqual(result["pending_cleanup"], [])

    def test_housekeeping_failures_do_not_block_delivery(self):
        self.record["cleanup_parent"] = str(self.worker.parent)
        self.record["ui"]["context"]["backend"] = "tmux"
        self.record["ui"]["agents"][0]["session"] = "$1"
        self.store()
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertEqual(len(result["housekeeping"]), 2)
        self.assertTrue(
            all(item["status"] == "pending" for item in result["housekeeping"])
        )

    def test_auto_removed_container_reuses_matching_exit_evidence(self):
        self.cli()
        self.env["CLI_MODE"] = "missing"
        result = self.cli()
        self.assertTrue(result["task_complete"])

    def test_ignored_generated_prompt_is_archived_and_worktree_removed(self):
        path = self.prompt()
        self.git(
            self.worker, "config", "core.excludesFile", str(self.root / "excludes")
        )
        (self.root / "excludes").write_text(".workmux/\n")
        result = self.cli()
        self.assertEqual(result["pending_cleanup"], [])
        self.assertFalse(path.exists())
        self.assertFalse(self.worker.exists())
        archived = self.path.parent / "archive" / path.name
        self.assertEqual(archived.read_text(), "generated")
        evidence = result["archives"]["archive:.workmux/" + path.name]
        self.assertEqual(evidence["handle"], "worker")
        self.assertEqual(
            evidence["files"][0]["sha256"],
            hashlib.sha256(archived.read_bytes()).hexdigest(),
        )

    def test_unknown_ignored_prompt_preserved_after_known_prompt_archived(self):
        known = self.prompt()
        unknown = known.with_name("PROMPT-not-in-receipt.md")
        unknown.write_text("preserve me")
        (self.repo / ".git/info/exclude").write_text(".workmux/\n")
        result = self.cli()
        self.assertFalse(known.exists())
        self.assertEqual(unknown.read_text(), "preserve me")
        self.assertTrue(self.worker.exists())
        self.assertFalse(result["cleanup_complete"])
        self.assertFalse(result["finish_complete"])
        self.assertTrue(
            any(item["identity"] == str(unknown) for item in result["pending_cleanup"])
        )
        self.assertEqual(result["housekeeping"][0]["status"], "pending")
        self.assertIn(
            "preserve its usable work tab", result["housekeeping"][0]["error"]
        )

    def test_failed_report_write_leaves_task_active(self):
        self.env["CLI_MODE"] = "report-error"
        # The runtime mode is shared by the fake CLIs; retain a running container
        # is not useful here, so make only Aven fail after an exited observation.
        binary = self.root / "bin/aven"
        original = binary.read_bytes()
        binary.write_text(
            "#!"
            + sys.executable
            + "\nimport sys\nsys.stderr.write('Aven unavailable')\nsys.exit(7)\n"
        )
        self.env["CLI_MODE"] = "exited"
        result = self.cli(ok=False)
        self.assertFalse(result["task_complete"])
        self.assertFalse(result["delivered"])
        self.assertIn("Aven unavailable", result["error"])
        self.assertNotIn("task", result["actions"])
        report = self.path.parent / "completion.md"
        self.assertEqual(result["completion_report"], str(report))
        self.assertIn("VERIFIED:", report.read_text())
        self.assertIn(
            self.git(self.repo, "rev-parse", "--short", "HEAD"), report.read_text()
        )
        binary.write_bytes(original)
        self.assertTrue(self.cli()["task_complete"])

    def test_finish_does_not_read_acceptance_evidence(self):
        self.verification.write_text("not valid JSON")
        self.record["integration"]["ok"] = False
        self.record["acceptance_checks"] = [["false"]]
        self.store()
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertFalse(self.worker.exists())

    def test_missing_acceptance_evidence_does_not_block_closure(self):
        self.verification.unlink()
        self.assertTrue(self.cli()["task_complete"])
        self.assertFalse(self.worker.exists())

    def test_wrong_worktree_branch_is_not_removed(self):
        self.git(self.worker, "switch", "-c", "unrelated")
        self.assertIn("identity changed", self.cli(ok=False)["error"])
        self.assertTrue(self.worker.exists())

    def test_replaced_git_directory_preserves_prompt(self):
        prompt = self.prompt()
        unrelated = self.root / "unrelated"
        unrelated.mkdir()
        self.git(unrelated, "init", "-b", "main")
        (self.worker / ".git").write_text(f"gitdir: {unrelated / '.git'}\n")
        result = self.cli(ok=False)
        self.assertIn("identity", result["error"])
        self.assertTrue(prompt.exists())
        self.assertTrue((unrelated / ".git").exists())

    def test_primary_worktree_is_never_removed(self):
        self.record["worktree"] = str(self.repo)
        self.store()
        self.cli(ok=False)
        self.assertTrue((self.repo / "file").exists())

    def test_tracked_prompts_are_retained(self):
        path = self.prompt()
        self.git(self.worker, "add", str(path))
        result = self.cli()
        self.assertTrue(path.exists())
        self.assertTrue(result["pending_cleanup"])

    def test_read_only_inspection_does_not_change_record(self):
        before = self.path.read_bytes()
        result = self.cli("--inspect")
        self.assertTrue(result["writer"]["stopped"])
        self.assertEqual(before, self.path.read_bytes())
        self.assertTrue(self.worker.exists())

    def test_interrupted_archive_uses_verified_copy(self):
        source = self.prompt()
        (self.worker / "unknown").write_text("retain")
        self.cli()
        record = json.loads(self.path.read_text())
        record["finish"]["actions"]["archive:.workmux/PROMPT-one.md"] = "attempted"
        self.path.write_text(json.dumps(record))
        self.assertFalse(source.exists())
        (self.worker / "unknown").unlink()
        result = self.cli()
        self.assertEqual(result["pending_cleanup"], [])

    def aven_mutations(self):
        return [
            call
            for line in Path(self.env["CALL_LOG"]).read_text().splitlines()
            if (call := json.loads(line))[0] == "aven" and call[1] != "context"
        ]

    def test_repeated_finish_does_not_repeat_task_mutations(self):
        self.cli()
        before = self.aven_mutations()
        self.cli()
        self.assertEqual(self.aven_mutations(), before)
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "done")

    def test_failed_status_write_is_visible_and_recoverable(self):
        self.env["FINISH_AVEN_MODE"] = "status-error"
        result = self.cli(ok=False)
        self.assertTrue(result["delivered"])
        self.assertFalse(result["task_complete"])
        self.assertEqual(result["actions"]["task"], "attempted")
        self.assertIn("status store unavailable", result["error"])
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "active")
        self.assertTrue((self.path.parent / "completion.md").exists())
        blocker = json.loads(self.path.read_text())["finish_blocker"]
        self.assertEqual(blocker["owner"], "dispatcher")
        self.assertTrue(blocker["next_action"])
        self.assertIn("BLOCKED:", Path(blocker["report"]).read_text())
        del self.env["FINISH_AVEN_MODE"]
        self.assertTrue(self.cli()["task_complete"])
        self.assertNotIn("finish_blocker", json.loads(self.path.read_text()))

    def test_status_write_requires_readback_confirmation(self):
        self.env["FINISH_AVEN_MODE"] = "status-noop"
        result = self.cli(ok=False)
        self.assertFalse(result["task_complete"])
        self.assertIn("not confirmed done", result["error"])
        del self.env["FINISH_AVEN_MODE"]
        self.assertTrue(self.cli()["task_complete"])

    def test_completed_record_reconciles_actual_active_status(self):
        self.cli()
        state = json.loads(self.aven_state.read_text())
        state["status"] = "active"
        self.aven_state.write_text(json.dumps(state))
        self.assertTrue(self.cli()["task_complete"])
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "done")

    def test_interrupted_status_write_reconciles_without_duplicate_mutation(self):
        self.env["FINISH_AVEN_MODE"] = "interrupted-write"
        self.cli(ok=False)
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "done")
        before = self.aven_mutations()
        del self.env["FINISH_AVEN_MODE"]
        self.assertTrue(self.cli()["task_complete"])
        self.assertEqual(self.aven_mutations(), before)

    def test_canceled_task_requires_dispatcher_judgment(self):
        self.aven_state.write_text(json.dumps({"status": "canceled", "notes": []}))
        result = self.cli(ok=False)
        self.assertFalse(result["task_complete"])
        self.assertIn("judgment required", result["error"])
        self.assertEqual(json.loads(self.aven_state.read_text())["status"], "canceled")
        self.assertFalse(any(call[1] == "edit" for call in self.aven_mutations()))

    def test_status_read_failure_never_claims_completion(self):
        self.env["FINISH_AVEN_MODE"] = "read-error"
        result = self.cli(ok=False)
        self.assertFalse(result["task_complete"])
        self.assertIn("status read unavailable", result["error"])
        del self.env["FINISH_AVEN_MODE"]
        self.assertTrue(self.cli()["task_complete"])

    def test_auto_removal_after_stop_is_confirmed_and_saved(self):
        binary = self.root / "bin/docker"
        state = self.root / "stopped"
        binary.write_text(
            "#!"
            + sys.executable
            + "\n"
            + """
import json, sys
from pathlib import Path
state = Path(STATE)
if sys.argv[1] == "inspect":
    if state.exists():
        sys.exit(1)
    print(json.dumps([{"Id": "container-1", "State": {"Status": "running"},
                      "Mounts": [{"Type": "bind", "Source": WORKER, "Destination": "/worker"}]}]))
elif sys.argv[1] == "stop":
    state.write_text("stopped")
elif sys.argv[1] == "ps":
    print("")
else:
    sys.exit(8)
""".replace("STATE", repr(str(state))).replace("WORKER", repr(str(self.worker)))
        )
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertTrue(state.exists())
        self.assertTrue(
            any(
                "listed_container_ids" in item
                for item in result["stop"]["observations"]
            )
        )
        self.cli()

    def test_failed_branch_removal_is_pending_and_retry_only_removes_branch(self):
        real_git = shutil.which("git")
        binary = self.root / "bin/git"
        binary.write_text(
            "#!"
            + sys.executable
            + "\n"
            + """
import os, sys
if "branch" in sys.argv and "-d" in sys.argv:
    sys.exit(7)
os.execv(REAL, [REAL, *sys.argv[1:]])
""".replace("REAL", repr(real_git))
        )
        binary.chmod(0o755)
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertFalse(self.worker.exists())
        self.assertEqual(result["pending_cleanup"][0]["resource"], "branch")
        binary.unlink()
        self.assertEqual(self.cli()["pending_cleanup"], [])

    def test_matching_pane_in_unknown_tmux_server_is_not_closed(self):
        self.record["ui"] = {
            "context": {"backend": "tmux"},
            "agents": [{"pane_id": "%1", "session": "$1"}],
        }
        self.store()
        log = self.root / "tmux-calls"
        binary = self.root / "bin/tmux"
        binary.write_text(
            "#!"
            + sys.executable
            + "\nimport sys\nfrom pathlib import Path\n"
            + f"with Path({str(log)!r}).open('a') as out:\n"
            + "    out.write(repr(sys.argv[1:]) + '\\n')\n"
            + f"print({('%1' + chr(9) + '$1' + chr(9) + str(self.worker))!r})\n"
        )
        binary.chmod(0o755)
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertEqual(result["housekeeping"][0]["status"], "pending")
        self.assertNotIn("kill-pane", log.read_text() if log.exists() else "")

    def test_tmux_closure_requires_matching_server_and_pane(self):
        for endpoint, status in (
            ("/original.sock", "pending"),
            ("/other.sock", "pending"),
        ):
            with self.subTest(socket=endpoint):
                self.record["ui"] = {
                    "context": {"backend": "tmux", "socket_path": "/original.sock"},
                    "agents": [{"pane_id": "%1", "session": "$1"}],
                }
                self.store()
                log = self.root / "tmux-calls"
                binary = self.root / "bin/tmux"
                actual = "\t".join((endpoint, "%1", "$1", str(self.worker)))
                binary.write_text(
                    "#!"
                    + sys.executable
                    + "\nimport sys\nfrom pathlib import Path\n"
                    + f"with Path({str(log)!r}).open('a') as out:\n"
                    + "    out.write(repr(sys.argv[1:]) + '\\n')\n"
                    + f"print({actual!r})\n"
                )
                binary.chmod(0o755)
                # Retain the cleanly identified worker so each subtest can retry.
                (self.worker / "unknown").write_text("retain")
                result = self.cli()
                self.assertTrue(result["task_complete"])
                self.assertEqual(result["housekeeping"][0]["status"], status)
                self.assertFalse(result["cleanup_complete"])
                self.assertFalse(result["finish_complete"])
                self.assertNotIn("kill-pane", log.read_text() if log.exists() else "")
                if log.exists():
                    log.unlink()

    def test_completed_worktree_reappearing_requires_judgment(self):
        self.cli()
        self.git(
            self.repo, "worktree", "add", "-b", "worker", str(self.worker), self.base
        )
        result = self.cli(ok=False)
        self.assertIn("reappeared", result["error"])
        self.assertTrue(self.worker.exists())

    def test_completed_branch_reappearing_requires_judgment(self):
        self.cli()
        self.git(self.repo, "branch", "worker", self.base)
        result = self.cli(ok=False)
        self.assertIn("reappeared", result["error"])
        self.assertEqual(self.git(self.repo, "rev-parse", "worker"), self.base)

    def change_during_stop(self, root, *argv):
        binary = self.root / "bin/docker"
        marker = self.root / "changed-during-stop"
        binary.write_text(
            "#!"
            + sys.executable
            + "\n"
            + "import json, subprocess\nfrom pathlib import Path\n"
            + f"marker = Path({str(marker)!r})\n"
            + "if not marker.exists():\n"
            + f"    subprocess.run({['git', '-C', str(root), *argv]!r}, check=True)\n"
            + "    marker.touch()\n"
            + "print(json.dumps([{'Id': 'container-1', 'State': {'Status': 'exited'}, "
            + f"'Mounts': [{{'Type': 'bind', 'Source': {str(self.worker)!r}, "
            + "'Destination': '/worker'}]}]))\n"
        )

    def test_base_movement_during_stop_does_not_block_closure(self):
        prompt = self.prompt()
        self.change_during_stop(self.repo, "commit", "--allow-empty", "-qm", "moved")
        self.assertTrue(self.cli()["task_complete"])
        self.assertFalse(prompt.exists())
        self.assertFalse(self.worker.exists())

    def test_identity_change_during_stop_preserves_prompt(self):
        prompt = self.prompt()
        self.change_during_stop(self.worker, "switch", "-c", "unrelated")
        self.cli(ok=False)
        self.assertTrue(prompt.exists(), "Identity must be rechecked before archival")
        self.assertTrue(self.worker.exists())

    def test_unsafe_prompt_symlink_is_retained(self):
        path = self.prompt()
        path.unlink()
        path.symlink_to(self.repo / "file")
        result = self.cli()
        self.assertTrue(result["task_complete"])
        self.assertTrue(path.is_symlink())
        self.assertTrue(result["pending_cleanup"])


if __name__ == "__main__":
    unittest.main()
