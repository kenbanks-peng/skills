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


class CreateArgvTests(unittest.TestCase):
    def resolved(self):
        return [
            "container",
            "run",
            "--rm",
            "-it",
            "--name",
            "linux-random",
            "--memory",
            "16G",
            "--user",
            "501:20",
            "--mount",
            "type=bind,source=/work,target=/work",
            "--workdir",
            "/work",
            "--env",
            "HOME=/home/dev",
            "--env",
            "TOKEN=not-a-real-secret",
            "debian-dev:latest",
            "sleep",
            "infinity",
        ]

    def test_preserves_config_and_owns_identity(self):
        argv = MODULE.create_argv(self.resolved(), "dispatch-test", "owner")
        self.assertEqual(
            argv[:6],
            [
                "container",
                "create",
                "--name",
                "dispatch-test",
                "--label",
                "dispatch.owner=owner",
            ],
        )
        self.assertNotIn("--rm", argv)
        self.assertNotIn("-it", argv)
        self.assertNotIn("linux-random", argv)
        self.assertIn("TOKEN=not-a-real-secret", argv)
        self.assertEqual(argv[-3:], ["debian-dev:latest", "sleep", "infinity"])

    def test_rejects_other_runtime(self):
        argv = self.resolved()
        argv[0] = "docker"
        with self.assertRaises(ValueError):
            MODULE.create_argv(argv, "id", "owner")

    def test_rejects_unknown_flag(self):
        argv = self.resolved()
        argv[2:2] = ["--privileged"]
        with self.assertRaises(ValueError):
            MODULE.create_argv(argv, "id", "owner")

    def test_rejects_missing_name(self):
        argv = self.resolved()
        del argv[4:6]
        with self.assertRaises(ValueError):
            MODULE.create_argv(argv, "id", "owner")

    def test_rejects_duplicate_name(self):
        argv = self.resolved()
        argv[2:2] = ["--name", "another"]
        with self.assertRaises(ValueError):
            MODULE.create_argv(argv, "id", "owner")

    def test_does_not_parse_command_arguments_as_flags(self):
        argv = self.resolved()
        argv[-1] = "--name"
        with self.assertRaises(ValueError):
            MODULE.create_argv(argv, "id", "owner")

    def test_rejects_non_string_argv(self):
        with self.assertRaises(ValueError):
            MODULE.create_argv(["container", "run", None], "id", "owner")


class CreateIntentTests(unittest.TestCase):
    def invoke(self, root, failure=False, internal=False):
        worktree = root / "tree"
        common = worktree / ".git" if internal else root / "common"
        attempt = common / "dispatch" / "attempt"
        worktree.mkdir(exist_ok=True)
        attempt.mkdir(parents=True, exist_ok=True)
        resolved = CreateArgvTests().resolved()
        resolved[resolved.index("--mount") + 1] = (
            f"type=bind,source={worktree},target={worktree}"
        )
        resolved[resolved.index("--workdir") + 1] = str(worktree)
        argv = [
            "create_container.py",
            "--worktree",
            str(worktree),
            "--attempt",
            str(attempt),
        ]

        def runtime_run(command, **kwargs):
            record = json.loads((attempt / "container.json").read_text())
            self.assertEqual(record["phase"], "create-intent")
            self.assertEqual(command[command.index("--name") + 1], record["id"])
            if failure:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)

        with (
            patch("sys.argv", argv),
            patch.object(
                MODULE.shutil, "which", side_effect=lambda name: "/bin/" + name
            ),
            patch.object(
                MODULE,
                "capture",
                side_effect=[
                    str(common),
                    "Test Author <author@example.invalid> 1000 +0000",
                    "Test Committer <committer@example.invalid> 1000 +0000",
                    json.dumps(resolved),
                ],
            ),
            patch.object(MODULE.subprocess, "run", side_effect=runtime_run),
        ):
            MODULE.main()
        return attempt

    def test_intent_precedes_create_and_excludes_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            attempt = self.invoke(Path(directory).resolve())
            text = (attempt / "container.json").read_text()
            self.assertEqual(json.loads(text)["phase"], "created")
            self.assertNotIn("not-a-real-secret", text)
            self.assertEqual((attempt / "container.json").stat().st_mode & 0o777, 0o600)

    def test_failure_retains_intent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            with self.assertRaises(subprocess.CalledProcessError):
                self.invoke(root, failure=True)
            record = json.loads(
                (root / "common/dispatch/attempt/container.json").read_text()
            )
            self.assertEqual(record["phase"], "create-intent")

    def test_second_create_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            self.invoke(root)
            with self.assertRaisesRegex(ValueError, "Existing container intent"):
                self.invoke(root)

    def test_target_checkout_metadata_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            self.invoke(Path(directory).resolve(), internal=True)


if __name__ == "__main__":
    unittest.main()
