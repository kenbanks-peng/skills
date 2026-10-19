"""Finish CLI contracts with real Git and controlled external runtime responses."""

import hashlib
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import test_safety as safety


class FinishTests(unittest.TestCase):
    git = safety.SafetyTests.git

    def setUp(self):
        safety.SafetyTests.setUp(self)
        self.env["CLI_MODE"] = "exited"
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
                    "repo": {"common_dir": str(self.repo / ".git")},
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

    def test_one_authorization_finishes_and_repeated_finish_never_recreates(self):
        plan = self.cli()
        self.assertTrue(plan["dry_run"])
        self.assertTrue(self.worker.exists())
        result = self.cli("--authorize-finish")
        self.assertTrue(result["delivered"])
        self.assertTrue(result["task_complete"])
        self.assertFalse(self.worker.exists())
        self.assertEqual(result["pending_cleanup"], [])
        self.cli()
        self.assertFalse(self.worker.exists())
        self.assertTrue((self.path.parent / "completion.md").exists())

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
        result = self.cli("--authorize-finish", ok=False)
        self.assertFalse(result["delivered"])
        self.assertFalse(result["task_complete"])
        self.assertTrue(self.worker.exists())
        self.assertNotIn("aven", Path(self.env["CALL_LOG"]).read_text())

    def test_changed_prompt_is_pending_after_task_completion(self):
        path = self.prompt()
        path.write_text("changed")
        result = self.cli("--authorize-finish")
        self.assertTrue(result["task_complete"])
        self.assertEqual(path.read_text(), "changed")
        self.assertEqual(result["pending_cleanup"][0]["identity"], str(self.worker))
        self.assertEqual(result["pending_cleanup"][0]["owner"], "dispatcher")

    def test_dirty_and_unknown_files_remain_pending(self):
        (self.worker / "file").write_text("dirty")
        (self.worker / "unknown").write_text("retain")
        result = self.cli("--authorize-finish")
        self.assertTrue(result["task_complete"])
        self.assertTrue(result["pending_cleanup"])
        self.assertTrue((self.worker / "unknown").exists())

    def test_base_moved_blocks_cleanup_and_completion(self):
        self.git(self.repo, "commit", "--allow-empty", "-qm", "base moved")
        result = self.cli("--authorize-finish", ok=False)
        self.assertIn("Base moved", result["error"])
        self.assertTrue(self.worker.exists())

    def test_wrong_container_identity_blocks_completion(self):
        self.env["CLI_MODE"] = "wrong-id"
        result = self.cli("--authorize-finish", ok=False)
        self.assertFalse(result["task_complete"])
        self.assertTrue(self.worker.exists())

    def test_partial_archive_resumes_without_recreating_sources(self):
        path = self.prompt()
        (self.worker / "unknown").write_text("retain")
        first = self.cli("--authorize-finish")
        self.assertTrue(first["pending_cleanup"])
        self.assertFalse(path.exists())
        (self.worker / "unknown").unlink()
        second = self.cli()
        self.assertTrue(second["task_complete"])
        self.assertFalse(self.worker.exists())

    def test_partial_worktree_removal_resumes_branch_only(self):
        self.cli("--authorize-finish")
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
        result = self.cli("--authorize-finish")
        self.assertTrue(result["task_complete"])
        self.assertEqual(len(result["housekeeping"]), 2)
        self.assertTrue(
            all(item["status"] == "pending" for item in result["housekeeping"])
        )

    def test_auto_removed_container_reuses_matching_exit_evidence(self):
        self.cli("--authorize-finish")
        self.env["CLI_MODE"] = "missing"
        result = self.cli()
        self.assertTrue(result["task_complete"])

    def test_ignored_generated_prompt_is_retained(self):
        path = self.prompt()
        self.git(
            self.worker, "config", "core.excludesFile", str(self.root / "excludes")
        )
        (self.root / "excludes").write_text(".workmux/\n")
        result = self.cli("--authorize-finish")
        self.assertTrue(result["pending_cleanup"])
        self.assertTrue(path.exists())

    def test_failed_report_write_leaves_task_active(self):
        self.env["CLI_MODE"] = "report-error"
        # The runtime mode is shared by the fake CLIs; retain a running container
        # is not useful here, so make only Aven fail after an exited observation.
        binary = self.root / "bin/aven"
        binary.write_text("#!" + sys.executable + "\nimport sys\nsys.exit(7)\n")
        self.env["CLI_MODE"] = "exited"
        result = self.cli("--authorize-finish", ok=False)
        self.assertFalse(result["task_complete"])
        self.assertTrue((self.path.parent / "completion.md").exists())

    def test_mismatched_verification_blocks_actions(self):
        data = json.loads(self.verification.read_text())
        data["checks"][0]["argv"] = ["different-check"]
        self.verification.write_text(json.dumps(data))
        self.assertIn(
            "does not match", self.cli("--authorize-finish", ok=False)["error"]
        )
        self.assertTrue(self.worker.exists())

    def test_wrong_worktree_branch_is_not_removed(self):
        self.git(self.worker, "switch", "-c", "unrelated")
        self.assertIn(
            "identity changed", self.cli("--authorize-finish", ok=False)["error"]
        )
        self.assertTrue(self.worker.exists())

    def test_replaced_git_directory_preserves_prompt(self):
        prompt = self.prompt()
        unrelated = self.root / "unrelated"
        unrelated.mkdir()
        self.git(unrelated, "init", "-b", "main")
        (self.worker / ".git").write_text(f"gitdir: {unrelated / '.git'}\n")
        result = self.cli("--authorize-finish", ok=False)
        self.assertIn("identity", result["error"])
        self.assertTrue(prompt.exists())
        self.assertTrue((unrelated / ".git").exists())

    def test_primary_worktree_is_never_removed(self):
        self.record["worktree"] = str(self.repo)
        self.store()
        self.cli("--authorize-finish", ok=False)
        self.assertTrue((self.repo / "file").exists())

    def test_tracked_prompts_are_retained(self):
        path = self.prompt()
        self.git(self.worker, "add", str(path))
        result = self.cli("--authorize-finish")
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
        self.cli("--authorize-finish")
        record = json.loads(self.path.read_text())
        record["finish"]["actions"]["archive:.workmux/PROMPT-one.md"] = "attempted"
        self.path.write_text(json.dumps(record))
        self.assertFalse(source.exists())
        (self.worker / "unknown").unlink()
        result = self.cli()
        self.assertEqual(result["pending_cleanup"], [])

    def test_repeated_finish_does_not_repeat_task_mutations(self):
        self.cli("--authorize-finish")
        before = Path(self.env["CALL_LOG"]).read_text().count('"aven"')
        self.cli()
        self.assertEqual(Path(self.env["CALL_LOG"]).read_text().count('"aven"'), before)

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
        result = self.cli("--authorize-finish")
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
        result = self.cli("--authorize-finish")
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
            "#!" + sys.executable + "\nimport sys\nfrom pathlib import Path\n"
            + f"with Path({str(log)!r}).open('a') as out:\n"
            + "    out.write(repr(sys.argv[1:]) + '\\n')\n"
            + f"print({('%1' + chr(9) + '$1' + chr(9) + str(self.worker))!r})\n"
        )
        binary.chmod(0o755)
        result = self.cli("--authorize-finish")
        self.assertTrue(result["task_complete"])
        self.assertEqual(result["housekeeping"][0]["status"], "pending")
        self.assertNotIn("kill-pane", log.read_text() if log.exists() else "")

    def test_tmux_closure_requires_matching_server_and_pane(self):
        for socket, status in (("/original.sock", "closed"), ("/other.sock", "pending")):
            with self.subTest(socket=socket):
                self.record["ui"] = {
                    "context": {"backend": "tmux", "socket_path": "/original.sock"},
                    "agents": [{"pane_id": "%1", "session": "$1"}],
                }
                self.store()
                log = self.root / "tmux-calls"
                binary = self.root / "bin/tmux"
                actual = "\t".join((socket, "%1", "$1", str(self.worker)))
                binary.write_text(
                    "#!" + sys.executable + "\nimport sys\nfrom pathlib import Path\n"
                    + f"with Path({str(log)!r}).open('a') as out:\n"
                    + "    out.write(repr(sys.argv[1:]) + '\\n')\n"
                    + f"print({actual!r})\n"
                )
                binary.chmod(0o755)
                # Retain the cleanly identified worker so each subtest can retry.
                (self.worker / "unknown").write_text("retain")
                result = self.cli("--authorize-finish")
                self.assertTrue(result["task_complete"])
                self.assertEqual(result["housekeeping"][0]["status"], status)
                self.assertEqual("kill-pane" in log.read_text(), status == "closed")
                log.unlink()

    def test_completed_worktree_reappearing_requires_judgment(self):
        self.cli("--authorize-finish")
        self.git(self.repo, "worktree", "add", "-b", "worker", str(self.worker), self.base)
        result = self.cli(ok=False)
        self.assertIn("reappeared", result["error"])
        self.assertTrue(self.worker.exists())

    def test_completed_branch_reappearing_requires_judgment(self):
        self.cli("--authorize-finish")
        self.git(self.repo, "branch", "worker", self.base)
        result = self.cli(ok=False)
        self.assertIn("reappeared", result["error"])
        self.assertEqual(self.git(self.repo, "rev-parse", "worker"), self.base)

    def change_during_stop(self, root, *argv):
        binary = self.root / "bin/docker"
        marker = self.root / "changed-during-stop"
        binary.write_text(
            "#!" + sys.executable + "\n"
            + "import json, subprocess\nfrom pathlib import Path\n"
            + f"marker = Path({str(marker)!r})\n"
            + "if not marker.exists():\n"
            + f"    subprocess.run({['git', '-C', str(root), *argv]!r}, check=True)\n"
            + "    marker.touch()\n"
            + "print(json.dumps([{'Id': 'container-1', 'State': {'Status': 'exited'}, "
            + f"'Mounts': [{{'Type': 'bind', 'Source': {str(self.worker)!r}, "
            + "'Destination': '/worker'}]}]))\n"
        )

    def test_base_movement_during_stop_preserves_prompt(self):
        prompt = self.prompt()
        self.change_during_stop(self.repo, "commit", "--allow-empty", "-qm", "moved")
        self.cli("--authorize-finish", ok=False)
        self.assertTrue(prompt.exists(), "Base must be rechecked before archival")
        self.assertTrue(self.worker.exists())

    def test_identity_change_during_stop_preserves_prompt(self):
        prompt = self.prompt()
        self.change_during_stop(self.worker, "switch", "-c", "unrelated")
        self.cli("--authorize-finish", ok=False)
        self.assertTrue(prompt.exists(), "Identity must be rechecked before archival")
        self.assertTrue(self.worker.exists())

    def test_unsafe_prompt_symlink_is_retained(self):
        path = self.prompt()
        path.unlink()
        path.symlink_to(self.repo / "file")
        result = self.cli("--authorize-finish")
        self.assertTrue(result["task_complete"])
        self.assertTrue(path.is_symlink())
        self.assertTrue(result["pending_cleanup"])


if __name__ == "__main__":
    unittest.main()
