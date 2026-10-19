import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
FAKE = """#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
name = Path(sys.argv[0]).name
args = sys.argv[1:]
with open(os.environ["CALL_LOG"], "a") as log:
    log.write(json.dumps([name] + args) + "\\n")
if name == "tmux":
    if args[0] == "display-message": print("$3")
    elif args[0] == "new-window": print("@42")
elif name == "jq":
    print(json.load(sys.stdin)["result"]["root_pane"]["pane_id"])
elif args[:2] == ["tab", "create"]:
    print(json.dumps({"result": {"root_pane": {"pane_id": "pane-42"}}}))
elif args[:2] == ["pane", "run"]:
    sys.exit(int(os.environ.get("FAIL_RUN", "0")))
"""


class TasksTabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "calls.jsonl"
        for name in ("tmux", "herdr", "jq"):
            executable = self.root / name
            executable.write_text(FAKE, encoding="utf-8")
            executable.chmod(0o755)
        self.env = dict(
            os.environ,
            PATH=str(self.root) + os.pathsep + os.environ["PATH"],
            CALL_LOG=str(self.log),
        )
        for name in ("HERDR_ENV", "HERDR_WORKSPACE_ID", "TMUX"):
            self.env.pop(name, None)

    def run_script(self, script, *args):
        return subprocess.run(
            ["bash", str(SCRIPTS / script), *args],
            env=self.env,
            capture_output=True,
            text=True,
        )

    def calls(self):
        return (
            [json.loads(line) for line in self.log.read_text().splitlines()]
            if self.log.exists()
            else []
        )

    def test_tmux_round_trip(self):
        self.env["TMUX"] = "test-session"
        opened = self.run_script("open-tasks-tab.sh", str(self.root))
        self.assertEqual(opened.returncode, 0, opened.stderr)
        self.assertEqual(opened.stdout, "tmux:@42\n")
        closed = self.run_script("close-tasks-tab.sh", opened.stdout.strip())
        self.assertEqual(closed.returncode, 0, closed.stderr)
        self.assertEqual(self.calls()[-1], ["tmux", "kill-window", "-t", "@42"])
        self.assertIn("-P", self.calls()[1])

    def test_herdr_round_trip_and_precedence(self):
        self.env.update(
            HERDR_ENV="1", HERDR_WORKSPACE_ID="workspace-1", TMUX="also-set"
        )
        opened = self.run_script("open-tasks-tab.sh", str(self.root))
        self.assertEqual(opened.returncode, 0, opened.stderr)
        self.assertEqual(opened.stdout, "herdr:pane-42\n")
        closed = self.run_script("close-tasks-tab.sh", opened.stdout.strip())
        self.assertEqual(closed.returncode, 0, closed.stderr)
        self.assertEqual(self.calls()[-1], ["herdr", "pane", "close", "pane-42"])
        self.assertFalse(any(call[0] == "tmux" for call in self.calls()))

    def test_failed_herdr_start_retains_id(self):
        self.env.update(HERDR_ENV="1", HERDR_WORKSPACE_ID="workspace-1", FAIL_RUN="1")
        result = self.run_script("open-tasks-tab.sh", str(self.root))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "herdr:pane-42\n")
        self.assertFalse(any("close" in call for call in self.calls()))

    def test_rejects_unsafe_inputs_without_mutation(self):
        self.env["TMUX"] = "test-session"
        for args in (
            (),
            ("tasks",),
            ("tmux:tasks",),
            ("tmux:@1:2",),
            ("herdr:pane-42",),
        ):
            with self.subTest(args=args):
                self.assertNotEqual(
                    self.run_script("close-tasks-tab.sh", *args).returncode, 0
                )
        self.assertNotEqual(
            self.run_script("open-tasks-tab.sh", "relative/path").returncode, 0
        )
        del self.env["TMUX"]
        self.assertNotEqual(
            self.run_script("open-tasks-tab.sh", str(self.root)).returncode, 0
        )
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
