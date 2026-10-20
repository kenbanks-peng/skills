"""Public integration CLI tests: real Git, controlled Aven and Workmux."""

import fcntl
import json
import subprocess
import sys
import unittest
from pathlib import Path

import test_safety as safety

SCRIPTS = safety.SCRIPTS

FAKE = r"""#!PYTHON
import json, os, subprocess, sys
from pathlib import Path
args = sys.argv[1:]
repo, worker = os.environ["REPO"], os.environ["WORKER"]
def git(root, *argv):
    return subprocess.check_output(["git", "-C", root, *argv], text=True).strip()
if Path(sys.argv[0]).name == "aven":
    sha = os.environ.get("RESULT_SHA", git(worker, "rev-parse", "HEAD"))
    notes = [{"id": os.environ.get("RESULT_ID", "result-1"),
              "body": "RESULT: ready " + sha,
              "created_at": "2026-10-19T01:00:00Z"}]
    if os.environ.get("LATEST_BAD"):
        notes.append({"id": "result-2", "body": "RESULT: commit missing",
                      "created_at": "2026-10-19T02:00:00Z"})
    if os.environ.get("NO_RESULT"):
        notes = []
    print(json.dumps({"task": {"ref": "SKL-TEST"}, "notes": notes}))
elif args[0] == "list":
    print(json.dumps([{"handle": "worker", "branch": "worker",
                      "path": worker, "is_main": False}]))
elif args[0] == "merge":
    with open(os.environ["CALL_LOG"], "a") as out:
        out.write(json.dumps(args) + "\n")
    if os.environ.get("REWRITE"):
        if os.environ.get("CHANGE_TREE"):
            (Path(worker) / "new").write_text("unreviewed content")
            git(worker, "add", "new")
        git(worker, "commit", "--amend", "-qm", "rewritten")
    git(repo, "merge", "--ff-only", "worker")
    if os.environ.get("INTERRUPT"):
        sys.stderr.write("interrupted after integration")
        sys.exit(9)
else:
    sys.exit(8)
"""


class IntegrationTests(unittest.TestCase):
    git = safety.SafetyTests.git

    def setUp(self):
        safety.SafetyTests.setUp(self)
        self.env["REPO"] = str(self.repo)
        for name in ("aven", "workmux"):
            path = self.root / "bin" / name
            path.write_text(FAKE.replace("#!PYTHON", "#!" + sys.executable))
            path.chmod(0o755)
        (self.worker / "new").write_text("worker\n")
        self.git(self.worker, "add", "new")
        self.git(self.worker, "commit", "-qm", "worker")
        self.sha = self.git(self.worker, "rev-parse", "HEAD")
        self.path = self.repo / ".git/dispatch-workers/SKL-TEST/worker.json"
        self.path.parent.mkdir(parents=True)
        self.env["RESULT_SHA"] = self.sha
        self.record = {
            "schema_version": 1,
            "prior_note_ids": [],
            "task_ref": "SKL-TEST",
            "repo": str(self.repo),
            "common_dir": str(self.repo / ".git"),
            "worktree": str(self.worker),
            "branch": "worker",
            "base": "main",
            "handle": "worker",
            "routing": {},
            "events": [],
            "acceptance_checks": [[sys.executable, "-c", "print('checked')"]],
        }
        self.store()

    def store(self):
        self.path.write_text(json.dumps(self.record))

    def cli(self, *extra, ok=True):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "integrate.py"),
                "SKL-TEST",
                "--reviewed-commit",
                self.sha,
                "--result-id",
                "result-1",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stdout + result.stderr
        )
        return json.loads(result.stdout)

    def merged(self):
        return Path(self.env["CALL_LOG"]).exists()

    def test_success_keeps_worker_and_records_exact_checks(self):
        data = self.cli()
        self.assertTrue(self.worker.exists())
        self.assertEqual(data["integrated_worker_sha"], self.sha)
        self.assertEqual(data["verified_base_sha"], self.sha)
        evidence = json.loads(Path(data["verification_evidence"]).read_text())
        self.assertEqual(evidence["worker_sha"], self.sha)
        self.assertEqual(evidence["checks"][0]["stdout"], "checked\n")
        calls = Path(self.env["CALL_LOG"]).read_text()
        self.assertIn("--keep", calls)
        self.assertNotIn("--no-hooks", calls)
        self.assertNotIn("--no-verify", calls)
        self.assertNotIn("--rebase", calls)
        self.cli("--closure")
        logs = Path(data["evidence_directory"])
        self.assertTrue((logs / "worker-checks.json").exists())

    def test_check_failure_blocks_merge(self):
        self.record["acceptance_checks"] = [
            [sys.executable, "-c", "raise SystemExit(4)"]
        ]
        self.store()
        data = self.cli(ok=False)
        self.assertIn("Required checks failed", data["error"])
        self.assertFalse(self.merged())
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), self.base)
        log = Path(data["evidence_directory"]) / "worker-checks.json"
        self.assertEqual(json.loads(log.read_text())["checks"][0]["returncode"], 4)

    def test_missing_check_blocks_merge(self):
        self.record["acceptance_checks"] = [["dispatch-no-such-command"]]
        self.store()
        self.cli(ok=False)
        self.assertFalse(self.merged())

    def test_stale_result_blocks_merge(self):
        self.env["RESULT_ID"] = "new-result"
        self.assertIn("stale", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())

    def test_report_from_previous_worker_attempt_blocks_merge(self):
        self.record["prior_note_ids"] = ["result-1"]
        self.store()
        self.assertIn("predates", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())

    def test_missing_result_blocks_merge(self):
        self.env["NO_RESULT"] = "1"
        self.assertIn("No matching report", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())

    def test_result_with_wrong_commit_blocks_merge(self):
        self.env["RESULT_SHA"] = self.base
        self.assertIn("commit evidence", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())

    def test_result_accepts_git_generated_short_commit(self):
        self.env["RESULT_SHA"] = self.git(self.worker, "rev-parse", "--short", "HEAD")
        self.cli()

    def report(self, *args, ok=True):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "dispatch_cli.py"),
                "report",
                "--task",
                "SKL-TEST",
                *args,
            ],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stdout + result.stderr
        )
        return json.loads(result.stdout)

    def test_report_cli_returns_current_commit_and_record_without_extra_fields(self):
        data = self.report()
        self.assertEqual(data["worker_commit"], self.sha)
        self.assertEqual(data["record_path"], str(self.path))
        self.assertEqual(data["note"]["id"], "result-1")

    def test_report_cli_retains_invalid_result_and_never_falls_back(self):
        self.env["LATEST_BAD"] = "1"
        snapshot = self.root / "reports.json"
        self.assertIn(
            "commit evidence", self.report("--save", str(snapshot), ok=False)["error"]
        )
        self.assertEqual(len(json.loads(snapshot.read_text())["notes"]), 2)
        self.assertIn("commit evidence", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())

    def test_report_cli_can_reuse_retained_aven_response(self):
        snapshot = self.root / "reports.json"
        self.report("--save", str(snapshot))
        (self.root / "bin/aven").unlink()
        self.assertEqual(
            self.report("--input", str(snapshot))["worker_commit"], self.sha
        )

    def test_report_cli_rejects_previous_attempt_even_with_current_commit(self):
        self.record["prior_note_ids"] = ["result-1"]
        self.store()
        self.assertIn("predates", self.report(ok=False)["error"])

    def test_result_accepts_configured_short_unambiguous_commit(self):
        self.git(self.repo, "config", "core.abbrev", "4")
        self.env["RESULT_SHA"] = self.git(self.worker, "rev-parse", "--short", "HEAD")
        self.cli()

    def test_stale_commit_blocks_merge(self):
        self.git(self.worker, "commit", "--allow-empty", "-qm", "later")
        self.assertIn("stale", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())

    def test_conflict_retains_rebase_and_stops(self):
        (self.repo / "file").write_text("base change\n")
        self.git(self.repo, "commit", "-qam", "base change")
        (self.worker / "file").write_text("worker change\n")
        self.git(self.worker, "commit", "-qam", "worker change")
        self.sha = self.git(self.worker, "rev-parse", "HEAD")
        self.env["RESULT_SHA"] = self.sha
        self.cli(ok=False)
        self.assertTrue((self.repo / ".git/worktrees/worker/rebase-merge").exists())
        self.assertFalse(self.merged())
        self.cli("--new-attempt", ok=False)

    def test_interrupted_success_reconciles_without_second_merge(self):
        self.env["INTERRUPT"] = "1"
        failed = self.cli(ok=False)
        self.assertEqual(self.git(self.repo, "rev-parse", "HEAD"), self.sha)
        self.cli(ok=False)  # A repeated normal operation cannot merge again.
        data = self.cli("--reconcile")
        self.assertNotEqual(failed["evidence_directory"], data["evidence_directory"])
        self.assertTrue(
            (Path(failed["evidence_directory"]) / "worker-checks.json").exists()
        )
        self.assertTrue(data["ok"])
        self.assertEqual(len(Path(self.env["CALL_LOG"]).read_text().splitlines()), 1)

    def test_rewritten_commit_is_checked_again(self):
        self.env["REWRITE"] = "1"
        data = self.cli()
        self.assertTrue(data["worker_rewritten"])
        self.assertNotEqual(data["integrated_worker_sha"], self.sha)
        logs = Path(data["evidence_directory"])
        revised = json.loads((logs / "reconciled-worker-checks.json").read_text())
        self.assertEqual(revised["tested_sha"], data["integrated_worker_sha"])
        verified = json.loads(Path(data["verification_evidence"]).read_text())
        self.assertEqual(verified["worker_sha"], data["integrated_worker_sha"])

    def test_rebase_rewrite_captures_new_checked_commit(self):
        (self.repo / "base-only").write_text("base advance")
        self.git(self.repo, "add", "base-only")
        self.git(self.repo, "commit", "-qm", "base advance")
        data = self.cli()
        self.assertNotEqual(data["checked_worker_sha"], self.sha)
        self.assertEqual(data["checked_worker_sha"], data["integrated_worker_sha"])

    def test_base_movement_rejects_closure(self):
        self.cli()
        self.git(self.repo, "commit", "--allow-empty", "-qm", "later base")
        self.assertIn("Base moved", self.cli("--closure", ok=False)["error"])

    def test_base_movement_during_verification_blocks_success(self):
        code = (
            "import subprocess; "
            "b=subprocess.check_output(['git','branch','--show-current'],text=True).strip(); "
            f"r={str(self.repo)!r}; "
            "subprocess.run(['git','-C',r,'commit','--allow-empty','-qm','moved'],check=True) "
            "if subprocess.check_output(['git','-C',r,'rev-parse','main'],text=True).strip() "
            f"!= {self.base!r} else None"
        )
        self.record["acceptance_checks"] = [[sys.executable, "-c", code]]
        self.store()
        data = self.cli(ok=False)
        self.assertFalse(data["ok"])
        log = json.loads(
            (Path(data["evidence_directory"]) / "base-verification.json").read_text()
        )
        self.assertTrue(log["base_moved"])

    def test_repository_lock_blocks_mutation(self):
        with (self.repo / ".git/dispatch.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.cli(ok=False)
        self.assertFalse(self.merged())

    def test_base_metadata_mismatch_blocks_merge(self):
        self.git(self.repo, "config", "branch.worker.workmux-base", "other")
        self.cli(ok=False)
        self.assertFalse(self.merged())

    def test_rewritten_content_requires_new_review(self):
        self.env.update(REWRITE="1", CHANGE_TREE="1")
        data = self.cli(ok=False)
        self.assertIn("content differs", data["error"])
        self.assertTrue(self.worker.exists())

    def test_failed_check_on_rewritten_commit_cannot_succeed(self):
        self.env["REWRITE"] = "1"
        code = (
            "import subprocess; "
            "message=subprocess.check_output(['git','log','-1','--format=%s'],text=True); "
            "raise SystemExit(5 if message.strip() == 'rewritten' else 0)"
        )
        self.record["acceptance_checks"] = [[sys.executable, "-c", code]]
        self.store()
        data = self.cli(ok=False)
        self.assertTrue(data["worker_rewritten"])
        log = Path(data["evidence_directory"]) / "reconciled-worker-checks.json"
        self.assertEqual(json.loads(log.read_text())["checks"][0]["returncode"], 5)

    def test_worker_changes_and_unfinished_operations_block_merge(self):
        (self.worker / "untracked").write_text("keep")
        self.cli(ok=False)
        self.assertFalse(self.merged())
        (self.worker / "untracked").unlink()
        gitdir = Path(self.git(self.worker, "rev-parse", "--absolute-git-dir"))
        (gitdir / "MERGE_HEAD").write_text(self.base + "\n")
        self.cli("--new-attempt", ok=False)
        self.assertFalse(self.merged())
        self.assertTrue((gitdir / "MERGE_HEAD").exists())

    def test_changed_workmux_identity_blocks_merge(self):
        script = self.root / "bin/workmux"
        script.write_text(
            script.read_text().replace('"branch": "worker"', '"branch": "other"')
        )
        self.cli(ok=False)
        self.assertFalse(self.merged())

    def test_base_movement_during_worker_checks_blocks_merge(self):
        code = (
            "import subprocess; "
            f"subprocess.run(['git','-C',{str(self.repo)!r},"
            "'commit','--allow-empty','-qm','base moved'],check=True)"
        )
        self.record["acceptance_checks"] = [[sys.executable, "-c", code]]
        self.store()
        self.assertIn("Base moved", self.cli(ok=False)["error"])
        self.assertFalse(self.merged())
