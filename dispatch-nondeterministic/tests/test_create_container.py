import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "create_container", Path(__file__).parents[1] / "scripts/create_container.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LaunchTests(unittest.TestCase):
    def prepare(self, root, internal=False):
        worktree = root / "tree"
        common = worktree / ".git" if internal else root / "common"
        attempt = (worktree if internal else root / "project") / ".dispatch" / "attempt"
        worktree.mkdir(exist_ok=True)
        common.mkdir(exist_ok=True)
        attempt.mkdir(parents=True, exist_ok=True)
        with (
            patch(
                "sys.argv",
                ["helper", "--worktree", str(worktree), "--attempt", str(attempt)],
            ),
            patch.object(MODULE.shutil, "which", return_value="/bin/linux"),
            patch.object(MODULE, "capture", return_value=str(common)),
            patch.object(MODULE.subprocess, "run") as run,
        ):
            self.assertEqual(MODULE.main(), 0)
            run.assert_not_called()
        return attempt

    def launch(self, attempt, rc=0, command=(), failure=False):
        path = attempt / "container.json"

        def run(argv, **kwargs):
            record = json.loads(path.read_text())
            self.assertEqual(record["phase"], "launch-intent")
            self.assertEqual(
                argv[:5], ["linux", "launch", "--name", record["id"], "-it"]
            )
            self.assertEqual(kwargs["cwd"], record["worktree"])
            self.assertNotIn("capture_output", kwargs)
            self.assertNotIn("--rm", argv)
            self.assertNotIn("sleep", argv)
            if failure:
                raise OSError("launch failed")
            return subprocess.CompletedProcess(argv, rc)

        with (
            patch(
                "sys.argv", ["helper", "--attempt", str(attempt), "--launch", *command]
            ),
            patch.object(MODULE.shutil, "which", return_value="/bin/linux"),
            patch.object(
                MODULE,
                "capture",
                side_effect=[
                    "Test Author <author@example.invalid> 1000 +0000",
                    "Test Committer <committer@example.invalid> 1000 +0000",
                ],
            ),
            patch.object(MODULE.subprocess, "run", side_effect=run) as call,
        ):
            result = MODULE.main()
        return result, call.call_args.args[0]

    def test_prepare_then_launch_pi(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.prepare(Path(tmp).resolve())
            path = attempt / "container.json"
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text())["phase"], "prepared")
            rc, argv = self.launch(attempt)
            self.assertEqual(rc, 0)
            self.assertEqual(
                argv[argv.index("--") + 1 :],
                [
                    "pi",
                    "--session",
                    f"{attempt}/pi.jsonl",
                    "--tui-mode",
                    "regular",
                    "--",
                    f"@{attempt}/prompt.md",
                ],
            )
            self.assertIn(f"GIT_CONFIG_VALUE_0={attempt.parents[2] / 'tree'}", argv)
            self.assertIn("GIT_AUTHOR_EMAIL=author@example.invalid", argv)
            self.assertNotIn("author@example.invalid", path.read_text())
            self.assertEqual(json.loads(path.read_text())["phase"], "exited")

    def test_check_command_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.prepare(Path(tmp).resolve())
            rc, argv = self.launch(
                attempt, rc=7, command=("--", "bash", str(attempt / "checks.sh"))
            )
            self.assertEqual(rc, 7)
            self.assertEqual(
                argv[argv.index("--") + 1 :], ["bash", str(attempt / "checks.sh")]
            )
            self.assertEqual(
                json.loads((attempt / "container.json").read_text())["exit_code"], 7
            )

    def test_launch_failure_retains_intent_and_refuses_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.prepare(Path(tmp).resolve())
            with self.assertRaises(OSError):
                self.launch(attempt, failure=True)
            self.assertEqual(
                json.loads((attempt / "container.json").read_text())["phase"],
                "launch-intent",
            )
            with self.assertRaisesRegex(ValueError, "Existing launch intent"):
                self.launch(attempt)

    def test_completed_launch_refuses_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.prepare(Path(tmp).resolve())
            self.launch(attempt)
            with self.assertRaisesRegex(ValueError, "Existing launch intent"):
                self.launch(attempt)

    def test_second_preparation_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            self.prepare(root)
            with self.assertRaises(FileExistsError):
                self.prepare(root)

    def test_source_directory_records_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            worktree = root / "tree"
            attempt = worktree / "src" / "attempt"
            attempt.mkdir(parents=True)
            common = worktree / ".git"
            common.mkdir()
            with (
                patch("sys.argv", ["helper", "--worktree", str(worktree),
                                   "--attempt", str(attempt)]),
                patch.object(MODULE.shutil, "which", return_value="/bin/linux"),
                patch.object(MODULE, "capture", return_value=str(common)),
                self.assertRaisesRegex(ValueError, "outside source files"),
            ):
                MODULE.main()
            self.assertFalse((attempt / "container.json").exists())

    def test_target_metadata_and_external_attempt_mount(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = self.prepare(Path(tmp).resolve(), internal=True)
            _, argv = self.launch(attempt)
            self.assertEqual(argv.count("-mount"), 1)
        record = {
            "id": "dispatch-test",
            "worktree": "/tree",
            "common_git": "/common",
            "attempt": "/records",
        }
        with patch.object(MODULE, "capture", return_value="A <a@b> 1000 +0000"):
            argv = MODULE.launch_argv(record, ["pi"])
        self.assertIn("/records:/records:rw", argv)
        self.assertEqual(argv.count("-mount"), 2)


if __name__ == "__main__":
    unittest.main()
