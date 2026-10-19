import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from worker_prompt import render

SCRIPT = Path(__file__).with_name("worker_prompt.py")
CONTRACT = SCRIPT.parent.parent / "worker.md"


def parameters():
    return {
        "task_ref": "SND-AG91",
        "project": "sandbox",
        "routing": "workspace default; preserve configured shared .aven routing",
        "branch": "demo-alpha",
        "base": "main",
        "launch_base": "a3e4654a91e4a601af2f57e6669ae45611630288",
        "objective": "Add exactly one line:\n<!-- demo worker alpha: concurrent dispatch -->",
        "write_scope": ["demo.md only, specifically the alpha comment"],
        "acceptance_checks": [
            "Own exact comment appears once",
            "git diff --check",
            "Only demo.md differs from launch base",
        ],
        "context": [
            "Preserve the beta worker's comment.",
            "Wait 30 seconds before editing.",
        ],
        "attachments": ["/tmp/context with spaces.md"],
    }


class WorkerPromptTests(unittest.TestCase):
    def test_renders_all_parameters_and_exact_contract(self):
        params = parameters()
        params["context"].append(
            "Literal `code`, $VAR, $(touch nope), ${VAR}\nand a new line"
        )
        contract = CONTRACT.read_text(encoding="utf-8")
        prompt = render(params, contract)
        for value in params.values():
            for item in value if isinstance(value, list) else [value]:
                self.assertIn(item, prompt)
        self.assertTrue(prompt.endswith(contract))
        self.assertEqual(prompt.count("# Worker contract"), 1)

    def test_optional_sections_are_omitted(self):
        params = parameters()
        del params["context"]
        del params["attachments"]
        prompt = render(params, "contract\n")
        self.assertNotIn("## Additional context", prompt)
        self.assertNotIn("## Attachments", prompt)

    def test_invalid_parameters(self):
        for field, value in (
            ("task_ref", " "),
            ("launch_base", "abc123"),
            ("write_scope", []),
            ("acceptance_checks", "git diff --check"),
            ("context", [3]),
            ("unexpected", "value"),
        ):
            with self.subTest(field=field):
                params = parameters()
                params[field] = value
                with self.assertRaises(ValueError):
                    render(params, "contract")
        with self.assertRaises(ValueError):
            render({}, "contract")
        with self.assertRaises(ValueError):
            render([], "contract")

    def test_cli_from_other_directory_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "params.json"
            output = root / "prompt.md"
            source.write_text(json.dumps(parameters()), encoding="utf-8")
            command = [
                sys.executable,
                str(SCRIPT.resolve()),
                "--params",
                str(source),
                "--output",
                str(output),
            ]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            expected = render(parameters(), CONTRACT.read_text(encoding="utf-8"))
            self.assertEqual(output.read_text(encoding="utf-8"), expected)
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), expected)
            source.write_text("{invalid", encoding="utf-8")
            output.unlink()
            result = subprocess.run(command, cwd=root, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
