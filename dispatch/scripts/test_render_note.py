import json
import tempfile
import unittest
from pathlib import Path

from render_note import render


class NoteTests(unittest.TestCase):
    def test_dispatch_is_compact(self):
        note = render("DISPATCH", dict(
            task_ref="SND-1234", handle="demo", branch="demo",
            worktree=str(Path.home() / "Sandbox__worktrees/demo"),
            base="main", launch_base="abc1234", agent_type="pi",
            config="run context", execution_mode="run context",
        ))
        self.assertTrue(note.startswith("DISPATCH:"))
        self.assertNotIn("SND-1234", note)
        self.assertNotIn(str(Path.home()), note)
        self.assertLessEqual(len(note.splitlines()), 4)
        self.assertEqual(note.count("run context"), 1)

    def test_result_deduplicates_checks(self):
        note = render("RESULT", dict(
            task_ref="SND-1234", summary="Added comment.",
            worker_commit="abc1234", components=["demo.md", "demo.md"],
            checks=["comment occurs once", "comment occurs once"],
        ))
        self.assertEqual(note.count("comment occurs once"), 1)
        self.assertEqual(note.count("demo.md"), 1)
        self.assertNotIn("Task:", note)

    def test_closure_keeps_validation_without_dumping_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            params = dict(task_ref="SND-1234", repo="/repo", base="main",
                          branch="demo", worktree="/worker",
                          worker_commit="a" * 40, verified_base_sha="b" * 40,
                          verification_evidence=str(root / "verify.json"),
                          cleanup_evidence=str(root / "cleanup.json"))
            verification = dict(
                ok=True, base_moved=False, tested_sha="b" * 40,
                worker_sha="a" * 40, repo=dict(worktree="/repo", common_dir="/git"),
                base_ref="refs/heads/main",
                checks=[dict(status="passed", returncode=0,
                             argv=["python3", "-c", "assert detail"])] * 2,
            )
            cleanup = dict(ok=True, executed=True, plan=dict(
                verified_base_sha="b" * 40, worker_commit="a" * 40,
                repo="/repo", common_dir="/git", base="main",
                branch="demo", worktree="/worker"))
            Path(params["verification_evidence"]).write_text(json.dumps(verification))
            Path(params["cleanup_evidence"]).write_text(json.dumps(cleanup))
            note = render("MERGE_VERIFIED", params)
            self.assertTrue(note.startswith("VERIFIED:"))
            self.assertNotIn("assert detail", note)
            self.assertNotIn("Recovery identity", note)
            self.assertIn("1 distinct check passed", note)
            self.assertLessEqual(len(note.splitlines()), 4)
            verification["checks"][0]["returncode"] = 1
            Path(params["verification_evidence"]).write_text(json.dumps(verification))
            with self.assertRaises(ValueError):
                render("MERGE_VERIFIED", params)


if __name__ == "__main__":
    unittest.main()
