import importlib.util
import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "container_state", Path(__file__).parents[1] / "scripts/container_state.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ContainerStateTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "id": "dispatch-test",
            "phase": "launch-intent",
            "worktree": "/tree",
            "common_git": "/common",
            "attempt": "/tree/.dispatch/run/w01/a01",
        }
        self.entry = {
            "configuration": {
                "id": "dispatch-test",
                "initProcess": {"workingDirectory": "/tree"},
                "mounts": [
                    {"source": path, "destination": path}
                    for path in ("/tree", "/common")
                ],
            },
            "status": {"state": "stopped"},
        }

    def state(self, record=None, entries=None):
        with patch.object(
            MODULE,
            "capture",
            return_value=json.dumps([self.entry] if entries is None else entries),
        ):
            return MODULE.owned_state(self.record if record is None else record)

    def test_matching_state(self):
        self.assertEqual(self.state(), "stopped")

    def test_common_git_attempt_needs_no_extra_mount(self):
        self.record["attempt"] = "/common/records/attempt"
        self.assertEqual(self.state(), "stopped")

    def test_prepared_receipt_is_not_ownership(self):
        self.record["phase"] = "prepared"
        with patch.object(MODULE, "capture") as capture:
            with self.assertRaisesRegex(ValueError, "No saved launch intent"):
                MODULE.owned_state(self.record)
            capture.assert_not_called()

    def test_mismatches_fail_closed(self):
        variants = []
        entry = deepcopy(self.entry)
        entry["configuration"]["id"] = "someone-else"
        variants.append(entry)
        entry = deepcopy(self.entry)
        entry["configuration"]["initProcess"]["workingDirectory"] = "/other"
        variants.append(entry)
        entry = deepcopy(self.entry)
        entry["configuration"]["mounts"].pop()
        variants.append(entry)
        entry = deepcopy(self.entry)
        entry["configuration"]["mounts"][0]["destination"] = "/other"
        variants.append(entry)
        for entries in ([], [self.entry, self.entry], *([v] for v in variants)):
            with self.subTest(entries=entries), self.assertRaises(ValueError):
                self.state(entries=entries)

    def test_external_attempt_requires_its_mount(self):
        self.record["attempt"] = "/records"
        with self.assertRaises(ValueError):
            self.state()
        self.entry["configuration"]["mounts"].append(
            {"source": "/records", "destination": "/records"}
        )
        self.assertEqual(self.state(), "stopped")

    def invoke(self, action, states=("stopped",), listing="[]"):
        with (
            patch("sys.argv", ["state", "--attempt", "/records", action]),
            patch.object(MODULE, "load_record", return_value=self.record),
            patch.object(MODULE, "owned_state", side_effect=states),
            patch.object(MODULE, "capture", return_value=listing),
            patch.object(MODULE.subprocess, "run") as run,
        ):
            MODULE.main()
        return run

    def test_stop_checks_before_and_after(self):
        run = self.invoke("stop", states=("running", "stopped"))
        self.assertEqual(
            run.call_args.args[0], ["linux", "stop", "--time", "10", "dispatch-test"]
        )

    def test_stopped_stop_does_not_mutate(self):
        self.invoke("stop", states=("stopped", "stopped")).assert_not_called()

    def test_delete_requires_stopped(self):
        with (
            patch("sys.argv", ["state", "--attempt", "/records", "delete"]),
            patch.object(MODULE, "load_record", return_value=self.record),
            patch.object(MODULE, "owned_state", return_value="running"),
            patch.object(MODULE.subprocess, "run") as run,
        ):
            with self.assertRaises(ValueError):
                MODULE.main()
            run.assert_not_called()

    def test_delete_confirms_absence(self):
        run = self.invoke("delete")
        self.assertEqual(run.call_args.args[0], ["linux", "delete", "dispatch-test"])
        with self.assertRaises(ValueError):
            self.invoke("delete", listing='[{"id":"dispatch-test"}]')

    def test_connection_failure_does_not_prove_absence(self):
        with (
            patch("sys.argv", ["state", "--attempt", "/records", "delete"]),
            patch.object(MODULE, "load_record", return_value=self.record),
            patch.object(MODULE, "owned_state", return_value="stopped"),
            patch.object(MODULE.subprocess, "run"),
            patch.object(
                MODULE,
                "capture",
                side_effect=subprocess.CalledProcessError(1, ["linux"]),
            ),
            self.assertRaises(subprocess.CalledProcessError),
        ):
            MODULE.main()

    def test_receipt_path_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            attempt = Path(tmp).resolve()
            (attempt / "container.json").write_text(json.dumps(self.record))
            with self.assertRaises(ValueError):
                MODULE.load_record(attempt)


if __name__ == "__main__":
    unittest.main()
