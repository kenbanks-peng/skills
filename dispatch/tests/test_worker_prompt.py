"""Worker prompts fetch plain task context from Aven."""

import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from worker_prompt import render  # noqa: E402


class WorkerPromptTests(unittest.TestCase):
    context = (
        "APP-TEST: Improve worker assignments\n"
        "Status: active\nDescription:\n"
        "First line\n  indented second line\n\nNotes:\n"
        "DECISION: use supplied context\n"
    )

    def assignment(self):
        return {
            "base": "main",
            "launch_base": "a" * 40,
            "branch": "dispatch/app-test",
            "write_scope": ["src/file.py", "tests/test file.py"],
            "acceptance_checks": [["python3", "-m", "unittest"], ["git", "diff", "--check"]],
            "routing": {},
            "repo": "/example/repo",
        }

    def test_complete_readable_assignment(self):
        with patch("worker_prompt.run", return_value=self.context) as run:
            prompt = render("APP-TEST", **self.assignment())
        run.assert_called_once_with(["aven", "context", "APP-TEST"], "/example/repo")
        for value in (
            "# Worker assignment: APP-TEST",
            "Complete the task below within the assigned write scope.",
            "Task ref: APP-TEST", "Base branch: main",
            "Launch-base commit: " + "a" * 40, "Worker branch: dispatch/app-test",
            "- src/file.py\n- tests/test file.py",
            "    python3 -m unittest\n\n    git diff --check",
            "- db: configured default\n- workspace: configured default",
            self.context,
        ):
            self.assertIn(value, prompt)
        self.assertNotIn("```", prompt)
        self.assertNotIn("literal assignment data", prompt)
        self.assertEqual(prompt.count("# Worker contract"), 1)
        self.assertIn("RESULT:", prompt)
        self.assertIn("BLOCKED:", prompt)
        self.assertTrue(prompt.endswith((Path(__file__).resolve().parents[1] / "worker.md").read_text()))

    def test_task_reference_and_routing_are_passed_to_aven(self):
        assignment = self.assignment()
        assignment["routing"] = {"db": "/host/tasks db", "workspace": "explicit"}
        with patch("worker_prompt.run", return_value=self.context) as run:
            prompt = render("DSP-A7PE", **assignment)
        run.assert_called_once_with(
            ["aven", "context", "DSP-A7PE", "--db", "/host/tasks db", "--workspace", "explicit"],
            "/example/repo",
        )
        self.assertIn("- db: /host/tasks db\n- workspace: explicit", prompt)

    def test_check_argument_fidelity_without_shell_execution(self):
        assignment = self.assignment()
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "SENTINEL"
            argv = [
                "tool", "", "two words", "single'quote", 'double"quote',
                "$HOME", "`uname`", "$(touch " + str(sentinel) + ")",
                "; echo bad", "*.py", "back\\slash", "first\nsecond",
            ]
            assignment["acceptance_checks"] = [argv]
            with patch("worker_prompt.run", return_value=self.context):
                prompt = render("APP-TEST", **assignment)
            block = prompt.split("Run each command exactly as shown, in this order:\n\n", 1)[1]
            command = block.split("\n\n## Aven reporting", 1)[0]
            command = "\n".join(line[4:] for line in command.splitlines())
            self.assertEqual(shlex.split(command), argv)
            self.assertFalse(sentinel.exists())

    def test_context_is_preserved_without_added_fences(self):
        context = "Description:\nUse `code` and $HOME\n\n- First item\n  continuation"
        with patch("worker_prompt.run", return_value=context):
            prompt = render("APP-TEST", **self.assignment())
        self.assertIn("## Task context\n\n" + context, prompt)
        self.assertNotIn("```", prompt)

    def test_context_failure_stops_rendering(self):
        with patch("worker_prompt.run", side_effect=ValueError("cannot read context")):
            with self.assertRaisesRegex(ValueError, "cannot read context"):
                render("APP-TEST", **self.assignment())


if __name__ == "__main__":
    unittest.main()
