"""Run the local renderer CLI in isolation. This is not native TML acceptance."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/dashboard.py"


def apply_patch(state, operations):
    """Small test interpreter for the helper's test/replace-only patch contract."""
    result = copy.deepcopy(state)
    for op in operations:
        keys = op["path"].strip("/").split("/")
        parent = result
        for key in keys[:-1]:
            parent = parent[key]
        if op["op"] == "test":
            if parent[keys[-1]] != op["value"]:
                raise ValueError("guard failed")
        elif op["op"] == "replace":
            if keys[-1] not in parent:
                raise ValueError("replace target missing")
            parent[keys[-1]] = op["value"]
        else:
            raise ValueError("unexpected patch operation")
    return result


class HelperCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.before = json.loads((ROOT / "assets/dashboard-example.json").read_text())

    def save(self, name, value):
        path = self.directory / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                              cwd=self.directory, capture_output=True, text=True, timeout=10)

    def test_lifecycle_projection_patch_and_stale_guard(self):
        before_path = self.save("before.json", self.before)
        after = copy.deepcopy(self.before)
        after["revision"] += 1
        after["observed_at"] = "fixture observation 2"
        row = after["tasks"][0]
        row.update(task_state="done", dependencies=["fixture dependency: done"],
                   queue="fixture q1 completed once", review="fixture accepted",
                   checks="fixture byte check: exit 0", delivery="fixture squash SHA",
                   cleanup="fixture tree removed; branch retained", blockers="none")
        row["native"].update(state="done", source="report", completion_seq=2)
        after_path = self.save("after.json", after)
        result = self.cli("render", before_path)
        self.assertEqual(result.returncode, 0, result.stderr)
        state = json.loads(ET.fromstring(result.stdout).find("state").text)
        patch_result = self.cli("patch", before_path, after_path)
        self.assertEqual(patch_result.returncode, 0, patch_result.stderr)
        operations = json.loads(patch_result.stdout)
        updated = apply_patch(state, operations)
        rendered = self.cli("render", after_path)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        self.assertEqual(updated, json.loads(ET.fromstring(rendered.stdout).find("state").text))
        old_state = copy.deepcopy(updated)
        with self.assertRaisesRegex(ValueError, "guard failed"):
            apply_patch(updated, operations)
        self.assertEqual(updated, old_state)
        self.assertEqual({p.name for p in self.directory.iterdir()}, {"before.json", "after.json"})

    def test_untrusted_content_is_data_and_has_no_side_effect(self):
        payload = '<button on-press="exec">$(touch PWNED)</button> & {state.secret}'
        self.before["tasks"][0]["checks"] = payload
        source = self.save("input.json", self.before)
        result = self.cli("render", source)
        self.assertEqual(result.returncode, 0, result.stderr)
        root = ET.fromstring(result.stdout)
        self.assertEqual(json.loads(root.find("state").text)["board"]["tasks"][0]["checks"], payload)
        self.assertEqual(list(root.iter("button")), [])
        self.assertFalse((self.directory / "PWNED").exists())
        self.assertEqual(source.read_text(), json.dumps(self.before))

    def test_cli_rejects_invalid_or_cross_run_update_without_output(self):
        before = self.save("before.json", self.before)
        after = copy.deepcopy(self.before)
        after["revision"] += 1
        after["run"] = "different run"
        for args in (("render", self.directory / "absent.json"),
                     ("patch", before, before),
                     ("patch", before, self.save("other.json", after)),
                     ("render", self.save("invalid.json", {"run": "bad"}))):
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.startswith("dashboard:"))


if __name__ == "__main__":
    unittest.main()
