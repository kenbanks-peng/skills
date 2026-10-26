"""Worker prompts fetch plain task context from Aven."""

import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dispatch_lib.prompts import render  # noqa: E402


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
            "acceptance_checks": [
                ["python3", "-m", "unittest"],
                ["git", "diff", "--check"],
            ],
        }

    def test_complete_readable_assignment(self):
        with patch("dispatch_lib.prompts.run", return_value=self.context) as run:
            prompt = render("APP-TEST", **self.assignment())
        run.assert_called_once_with(["aven", "context", "APP-TEST"])
        for value in (
            "Task ref: APP-TEST",
            "Base branch: main",
            "Launch-base commit: " + "a" * 40,
            "Worker branch: dispatch/app-test",
            "    python3 -m unittest\n\n    git diff --check",
            self.context,
        ):
            self.assertIn(value, prompt)
        self.assertNotIn("```", prompt)
        self.assertNotIn("literal assignment data", prompt)
        self.assertEqual(prompt.count("# Worker contract"), 1)
        self.assertIn("RESULT:", prompt)
        self.assertIn("BLOCKED:", prompt)
        self.assertIn(
            (Path(__file__).resolve().parents[1] / "worker.md").read_text().rstrip(),
            prompt,
        )
        self.assertTrue(prompt.startswith("## Work location\n"))
        self.assertLess(
            prompt.index("## Task context"), prompt.index("# Worker contract")
        )
        self.assertLess(
            prompt.index("# Worker contract"), prompt.index("## Required checks")
        )
        self.assertNotIn("## Write scope", prompt)
        self.assertNotIn("## Aven reporting", prompt)

    def test_task_reference_is_passed_to_aven(self):
        with patch("dispatch_lib.prompts.run", return_value=self.context) as run:
            prompt = render("DSP-A7PE", **self.assignment())
        run.assert_called_once_with(["aven", "context", "DSP-A7PE"])
        self.assertIn("- Task ref: DSP-A7PE", prompt)

    def test_check_argument_fidelity_without_shell_execution(self):
        assignment = self.assignment()
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "SENTINEL"
            argv = [
                "tool",
                "",
                "two words",
                "single'quote",
                'double"quote',
                "$HOME",
                "`uname`",
                "$(touch " + str(sentinel) + ")",
                "; echo bad",
                "*.py",
                "back\\slash",
                "first\nsecond",
            ]
            assignment["acceptance_checks"] = [argv]
            with patch("dispatch_lib.prompts.run", return_value=self.context):
                prompt = render("APP-TEST", **assignment)
            block = prompt.split(
                "Run each command exactly as shown, in this order:\n\n", 1
            )[1]
            command = block.rstrip("\n")
            command = "\n".join(line[4:] for line in command.splitlines())
            self.assertEqual(shlex.split(command), argv)
            self.assertFalse(sentinel.exists())

    def test_context_is_preserved_without_added_fences(self):
        context = "Description:\nUse `code` and $HOME\n\n- First item\n  continuation"
        with patch("dispatch_lib.prompts.run", return_value=context):
            prompt = render("APP-TEST", **self.assignment())
        self.assertIn("## Task context\n\n" + context, prompt)
        self.assertNotIn("```", prompt)

    def test_context_failure_stops_rendering(self):
        with patch(
            "dispatch_lib.prompts.run", side_effect=ValueError("cannot read context")
        ):
            with self.assertRaisesRegex(ValueError, "cannot read context"):
                render("APP-TEST", **self.assignment())


if __name__ == "__main__":
    unittest.main()
