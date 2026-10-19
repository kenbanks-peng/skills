"""Safety contracts at the command interface; no live worker or container."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

# External CLI seam only. Git remains real. Every call is recorded.
FAKE_CLI = r"""#!PYTHON
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as out:
    out.write(json.dumps([name, *args]) + "\n")
mode = os.environ.get("CLI_MODE", "")
if name == "aven":
    if mode == "report-error":
        sys.stderr.write("report store unavailable")
        sys.exit(7)
    print(os.environ["AVEN_RESPONSE"])
elif name == "docker":
    if args[0] == "inspect":
        if mode == "missing":
            sys.exit(1)
        identity = "other" if mode == "wrong-id" else "container-1"
        mount = "/wrong" if mode == "wrong-mount" else os.environ["WORKER"]
        print(json.dumps([{
            "Id": identity,
            "State": {"Status": "exited" if mode == "exited" else "running"},
            "Mounts": [{"Type": "bind", "Source": mount, "Destination": "/worker"}]
        }]))
    elif args[0] == "ps":
        print("")
    elif args[0] == "stop":
        sys.stderr.write("stop failed")
        sys.exit(8)
else:
    sys.stderr.write("unexpected worker action")
    sys.exit(9)
"""


class SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dispatch-safety-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.repo = self.root / "repo"
        self.worker = self.root / "worker"
        self.repo.mkdir()
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Safety Test",
            GIT_AUTHOR_EMAIL="test@example.invalid",
            GIT_COMMITTER_NAME="Safety Test",
            GIT_COMMITTER_EMAIL="test@example.invalid",
            GIT_TERMINAL_PROMPT="0",
            PYTHONDONTWRITEBYTECODE="1",
            TMPDIR=str(self.root),
            CALL_LOG=str(self.root / "calls.jsonl"),
            WORKER=str(self.worker),
            CLI_MODE="",
            AVEN_RESPONSE=json.dumps({"task": {"ref": "SKL-TEST"}, "notes": []}),
        )
        binary = self.root / "bin"
        binary.mkdir()
        for name in ("aven", "docker", "workmux"):
            path = binary / name
            path.write_text(FAKE_CLI.replace("#!PYTHON", "#!" + sys.executable))
            path.chmod(0o755)
        self.env["PATH"] = str(binary) + os.pathsep + self.env["PATH"]
        self.git(self.repo, "init", "-b", "main")
        # Lifecycle subprocesses deliberately discard GIT_* environment overrides.
        # Keep commits/rebases independent of the host's global Git identity.
        self.git(self.repo, "config", "user.name", "Safety Test")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "file").write_text("base\n")
        (self.repo / ".gitignore").write_text("ignored\n")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "-qm", "base")
        self.base = self.git(self.repo, "rev-parse", "HEAD")
        self.git(self.repo, "worktree", "add", "-b", "worker", str(self.worker))
        self.git(self.repo, "config", "branch.worker.workmux-base", "main")

    def git(self, repo, *args):
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def json_file(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data))
        return str(path)

    def cli(self, script, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / script), *map(str, args)],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stderr + result.stdout
        )
        evidence = json.loads(result.stdout)
        self.assertIs(evidence["ok"], ok)
        return evidence

    def calls(self):
        path = self.root / "calls.jsonl"
        return (
            [json.loads(line) for line in path.read_text().splitlines()]
            if path.exists()
            else []
        )

    def assert_preserved(self, sha=None):
        self.assertTrue((self.worker / ".git").is_file())
        self.assertEqual(
            self.git(self.repo, "rev-parse", "refs/heads/worker"), sha or self.base
        )
        self.assertEqual(self.git(self.repo, "rev-parse", "refs/heads/main"), self.base)

    def preflight(self, ok=True, **overrides):
        values = {
            "repo": self.repo,
            "worker_worktree": self.worker,
            "worker_branch": "worker",
            "base": "main",
        }
        values.update(overrides)
        args = [
            item
            for key, value in values.items()
            for item in ("--" + key.replace("_", "-"), value)
        ]
        return self.cli("git_preflight.py", *args, ok=ok)

    def cleanup(self, ok=True, **overrides):
        values = {
            "repo": self.repo,
            "worktree": self.worker,
            "branch": "worker",
            "base": "main",
            "verified_base_sha": self.base,
            "worker_commit": self.base,
        }
        values.update(overrides)
        args = [
            item
            for key, value in values.items()
            for item in ("--" + key.replace("_", "-"), value)
        ]
        return self.cli(
            "cleanup_worker.py", *args, "--execute", "--authorize-cleanup", ok=ok
        )

    def verify(self, checks, ok=True, worker=None):
        return self.cli(
            "verify_base.py",
            "--repo",
            self.repo,
            "--base",
            "main",
            "--worker-commit",
            worker or self.base,
            "--checks-file",
            self.json_file("checks.json", checks),
            ok=ok,
        )

    def receipt(self):
        return {
            "schema_version": 1,
            "ok": True,
            "repo": str(self.repo),
            "worktree": str(self.worker),
            "worker_worktree": "/worker",
            "branch": "worker",
            "base": "main",
            "handle": "worker",
            "runtime": "docker",
            "container": {"id": "container-1"},
            "prompts": [],
        }

    def test_clean_preflight_and_authorized_cleanup(self):
        self.preflight()
        evidence = self.cleanup()
        self.assertEqual(len(evidence["actions"]), 2)
        self.assertFalse(self.worker.exists())
        self.assertEqual(self.git(self.repo, "branch", "--list", "worker"), "")

    def test_wrong_repository_base_and_worker_identity(self):
        other = self.root / "other"
        other.mkdir()
        self.git(other, "init", "-b", "main")
        (other / "file").write_text("other")
        self.git(other, "add", ".")
        self.git(other, "commit", "-qm", "other")
        for override in (
            {"repo": other},
            {"base": "missing"},
            {"worker_branch": "main"},
            {"worker_branch": "other-worker"},
            {"worker_worktree": self.worker / ".git"},
        ):
            with self.subTest(override=override):
                self.preflight(ok=False, **override)
                self.assert_preserved()
        self.git(self.repo, "config", "branch.worker.workmux-base", "wrong")
        evidence = self.preflight(ok=False)
        self.assertIn("explicit base", evidence["error"])
        self.assert_preserved()

    def test_dirty_and_hidden_files_block_removal(self):
        for filename in ("file", "untracked", "ignored"):
            with self.subTest(filename=filename):
                path = self.worker / filename
                original = path.read_bytes() if path.exists() else None
                path.write_text("evidence must survive")
                evidence = self.cleanup(ok=False)
                self.assertEqual(evidence["actions"], [])
                self.assertEqual(path.read_text(), "evidence must survive")
                self.assert_preserved()
                if filename != "ignored":
                    self.preflight(ok=False)
                if original is None:
                    path.unlink()
                else:
                    path.write_bytes(original)

    def test_unfinished_operations_and_live_lock_are_preserved(self):
        directory = Path(self.git(self.worker, "rev-parse", "--absolute-git-dir"))
        for marker in ("MERGE_HEAD", "rebase-merge", "index.lock"):
            with self.subTest(marker=marker):
                path = directory / marker
                path.mkdir() if marker == "rebase-merge" else path.write_text(
                    self.base + "\n"
                )
                if marker != "index.lock":
                    self.preflight(ok=False)
                evidence = self.cleanup(ok=False)
                self.assertEqual(evidence["actions"], [])
                self.assertTrue(path.exists())
                self.assert_preserved()
                path.rmdir() if path.is_dir() else path.unlink()

    def test_hidden_index_flags_block_removal(self):
        self.git(self.worker, "update-index", "--assume-unchanged", "file")
        self.preflight(ok=False)
        self.assertEqual(self.cleanup(ok=False)["actions"], [])
        self.assert_preserved()

    def test_stale_base_and_worker_revisions_block_removal(self):
        self.git(self.repo, "commit", "--allow-empty", "-qm", "base advanced")
        advanced = self.git(self.repo, "rev-parse", "HEAD")
        evidence = self.cleanup(ok=False)
        self.assertEqual(evidence["actions"], [])
        self.assertIn("Base changed", evidence["error"])
        self.assertTrue(self.worker.exists())
        self.assertEqual(self.git(self.repo, "rev-parse", "worker"), self.base)
        self.base = advanced
        self.git(self.worker, "commit", "--allow-empty", "-qm", "worker advanced")
        evidence = self.cleanup(ok=False)
        self.assertEqual(evidence["actions"], [])
        self.assertIn("commit mismatch", evidence["error"])
        self.assert_preserved(self.git(self.worker, "rev-parse", "HEAD"))

    def test_unmerged_work_cannot_be_verified_or_removed(self):
        self.git(self.worker, "commit", "--allow-empty", "-qm", "unmerged")
        worker = self.git(self.worker, "rev-parse", "HEAD")
        marker = self.root / "must-not-run"
        evidence = self.verify(
            [[sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"]],
            worker=worker,
            ok=False,
        )
        self.assertFalse(marker.exists())
        self.assertFalse(evidence["worker_is_ancestor"])
        evidence = self.cleanup(worker_commit=worker, ok=False)
        self.assertEqual(evidence["actions"], [])
        self.assert_preserved(worker)

    def test_failed_check_stops_next_check_and_retains_checkout(self):
        marker = self.root / "must-not-run"
        evidence = self.verify(
            [
                [
                    sys.executable,
                    "-c",
                    "import sys; print('failure evidence'); sys.exit(3)",
                ],
                [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"],
            ],
            ok=False,
        )
        self.assertFalse(marker.exists())
        self.assertEqual(evidence["checks"][1]["status"], "not_run")
        self.assertIn("failure evidence", evidence["checks"][0]["stdout"])
        self.assertEqual(evidence["cleanup"], "retained")
        self.assertTrue(Path(evidence["worktree"]).exists())
        self.assert_preserved()

    def test_base_movement_during_checks_blocks_success(self):
        code = (
            "import subprocess; subprocess.run("
            + repr(
                ["git", "-C", str(self.repo), "commit", "--allow-empty", "-qm", "moved"]
            )
            + ", check=True)"
        )
        evidence = self.verify([[sys.executable, "-c", code]], ok=False)
        self.assertTrue(evidence["base_moved"])
        self.assertTrue(Path(evidence["worktree"]).exists())
        self.assertTrue(self.worker.exists())

    def test_passing_checks_remove_only_verification_checkout(self):
        evidence = self.verify([[sys.executable, "-c", "pass"]])
        self.assertEqual(evidence["tested_sha"], self.base)
        self.assertFalse(Path(evidence["worktree"]).exists())
        self.assert_preserved()

    def test_missing_failed_stale_or_wrong_task_reports_fail_closed(self):
        for mode, data, extra in (
            ("", {"task": {"ref": "SKL-TEST"}, "notes": []}, []),
            ("report-error", {}, []),
            ("", {"task": {"ref": "SKL-OTHER"}, "notes": []}, []),
            (
                "",
                {
                    "task": {"ref": "SKL-TEST"},
                    "notes": [
                        {
                            "id": "1",
                            "created_at": "2026-01-01T00:00:00Z",
                            "body": "MERGE: old-id",
                        }
                    ],
                },
                ["--authorization", "new-id"],
            ),
        ):
            with self.subTest(mode=mode, data=data):
                self.env["CLI_MODE"] = mode
                self.env["AVEN_RESPONSE"] = json.dumps(data)
                self.cli(
                    "dispatch_cli.py",
                    "report",
                    "--task",
                    "SKL-TEST",
                    "--kind",
                    "MERGE",
                    *extra,
                    ok=False,
                )
                self.assert_preserved()
        self.assertTrue(all(call[0] == "aven" for call in self.calls()))

    def test_uncertain_exit_blocks_stop_and_cleanup(self):
        receipt = self.json_file("receipt.json", self.receipt())
        previous = self.json_file(
            "stop.json",
            {
                "ok": True,
                "stopped": True,
                "repo": str(self.repo),
                "worktree": str(self.worker),
                "handle": "worker",
                "container_id": "container-1",
            },
        )
        for mode in ("missing", "wrong-id", "wrong-mount", "running"):
            with self.subTest(mode=mode):
                self.env["CLI_MODE"] = mode
                evidence = self.cli(
                    "stop_worker.py", "--receipt", receipt, "--execute", ok=False
                )
                self.assertNotEqual(evidence.get("stopped"), True)
                # No previous proof for a missing container: absence alone cannot certify exit.
                if mode != "missing":
                    evidence = self.cleanup(
                        receipt=receipt, stop_evidence=previous, ok=False
                    )
                    self.assertEqual(evidence["actions"], [])
                self.assert_preserved()
        self.assertFalse(any(call[0] == "workmux" for call in self.calls()))

    def test_closure_rejects_failed_checks_stale_identity_and_dry_run(self):
        verification = self.verify([[sys.executable, "-c", "pass"]])
        cleanup = self.cli(
            "cleanup_worker.py",
            "--repo",
            self.repo,
            "--worktree",
            self.worker,
            "--branch",
            "worker",
            "--base",
            "main",
            "--verified-base-sha",
            self.base,
            "--worker-commit",
            self.base,
        )
        # A dry run must not be accepted as executed cleanup.
        params = {
            "base": "main",
            "verified_base_sha": self.base,
            "task_ref": "SKL-TEST",
            "verification_evidence": self.json_file("verification.json", verification),
            "cleanup_evidence": self.json_file("cleanup.json", cleanup),
            "repo": str(self.repo),
            "branch": "worker",
            "worktree": str(self.worker),
            "worker_commit": self.base,
        }

        def render(expected):
            output = self.root / "closure.md"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "render_note.py"),
                    "--kind",
                    "MERGE_VERIFIED",
                    "--params",
                    self.json_file("params.json", params),
                    "--output",
                    str(output),
                ],
                env=self.env,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(result.returncode, 0 if expected else 1, result.stderr)
            self.assertEqual(output.exists(), expected)
            if expected:
                self.assertIn("VERIFIED:", output.read_text())

        render(False)
        self.assert_preserved()
        # Use actual executed cleanup for the positive control.
        cleanup = self.cleanup()
        self.json_file("cleanup.json", cleanup)
        for change in ("failed-check", "stale-sha", "wrong-repo", "missing-evidence"):
            with self.subTest(change=change):
                changed = json.loads(json.dumps(verification))
                if change == "failed-check":
                    changed["checks"][0].update(status="failed", returncode=3)
                elif change == "stale-sha":
                    changed["tested_sha"] = "0" * 40
                elif change == "wrong-repo":
                    changed["repo"]["worktree"] = str(self.root)
                self.json_file("verification.json", changed)
                if change == "missing-evidence":
                    Path(params["verification_evidence"]).unlink()
                render(False)
        self.json_file("verification.json", verification)
        render(True)
        self.assertEqual(self.calls(), [])  # Rendering never changes task status.

    def test_matching_stopped_container_allows_cleanup(self):
        self.env["CLI_MODE"] = "exited"
        receipt = self.json_file("receipt.json", self.receipt())
        stopped = self.cli("stop_worker.py", "--receipt", receipt, "--execute")
        self.assertTrue(stopped["stopped"])
        self.cleanup(
            receipt=receipt, stop_evidence=self.json_file("stop.json", stopped)
        )
        self.assertFalse(self.worker.exists())


if __name__ == "__main__":
    unittest.main()
