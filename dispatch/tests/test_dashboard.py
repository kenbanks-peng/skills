"""Local schema and view tests. These tests do not validate with native tuios."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("dashboard", ROOT / "scripts/dashboard.py")
dash = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dash)


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = dash.load(ROOT / "assets/dashboard-example.json")

    def test_template_and_render_are_read_only(self):
        allowed = {"tml", "state", "scroll", "col", "heading", "text", "table", "column", "tabs", "tab"}
        for document in (dash.TEMPLATE.read_text(), dash.render(self.snapshot)):
            root = ET.fromstring(document)
            self.assertEqual(root.attrib["version"], "1")
            for node in root.iter():
                self.assertIn(node.tag, allowed)
                self.assertFalse(any(key.startswith("on-") for key in node.attrib))
                self.assertFalse(set(node.attrib) & {"bind", "submit", "key"})
                if node.tag == "table":
                    self.assertEqual(node.attrib["select"], "none")
            json.loads(root.find("state").text)

    def test_overview_is_compact_and_details_are_tabbed(self):
        root = ET.fromstring(dash.render(self.snapshot))
        tabs = list(root.iter("tab"))
        self.assertEqual([tab.attrib["id"] for tab in tabs],
                         ["overview", "work", "delivery", "resources"])
        overview = tabs[0].find("table")
        self.assertEqual([c.attrib["field"] for c in overview],
                         ["task", "state", "environment", "blockers"])
        for table in root.iter("table"):
            self.assertLessEqual(len(list(table)), 4)

    def test_all_fields_are_visible(self):
        root = ET.fromstring(dash.render(self.snapshot))
        columns = {node.attrib["field"] for node in root.iter("column")}
        self.assertEqual(columns, set(dash.TEXT_FIELDS) | set(dash.NATIVE_FIELDS) | {"dependencies"})
        self.assertIn("state.board.run", dash.render(self.snapshot))
        self.assertIn("state.board.observed_at", dash.render(self.snapshot))

    def test_escape_text_not_markup_or_bindings(self):
        payload = '<button on-press="close(1)">& \' {state.secret} </state> 雪'
        self.snapshot["tasks"][0]["blockers"] = payload
        self.snapshot["run"] = payload
        document = dash.render(self.snapshot)
        self.assertNotIn("<button", document)
        root = ET.fromstring(document)
        state = json.loads(root.find("state").text)
        self.assertEqual(state["board"]["tasks"][0]["blockers"], payload)
        self.assertEqual(state["board"]["run"], payload)
        self.assertFalse(list(root.iter("button")))

    def test_invalid_snapshots(self):
        invalid = [None, {}, {**self.snapshot, "extra": True},
                   {**self.snapshot, "revision": True}, {**self.snapshot, "tasks": {}},
                   {**self.snapshot, "observed_at": ""}]
        for field, value in (("task", ""), ("dependencies", "TASK-0"),
                             ("blockers", "bad\x00"), ("native", {})):
            sample = copy.deepcopy(self.snapshot)
            sample["tasks"][0][field] = value
            invalid.append(sample)
        for field, value in (("state", "running"), ("state", []),
                             ("evidence_age_ms", -1), ("subagents", True)):
            sample = copy.deepcopy(self.snapshot)
            sample["tasks"][0]["native"][field] = value
            invalid.append(sample)
        duplicate = copy.deepcopy(self.snapshot)
        duplicate["tasks"] *= 2
        invalid.append(duplicate)
        for sample in invalid:
            with self.subTest(sample=sample), self.assertRaises(ValueError):
                dash.render(sample)

    def test_empty_tasks_and_competing_attempts(self):
        self.assertEqual(dash.board({**self.snapshot, "tasks": []})["tasks"], [])
        other = copy.deepcopy(self.snapshot["tasks"][0])
        other["attempt"] = "a02"
        self.snapshot["tasks"].append(other)
        self.assertEqual(len(dash.board(self.snapshot)["tasks"]), 2)

    def test_patch_updates_same_state_with_guard(self):
        current = copy.deepcopy(self.snapshot)
        current["revision"] += 1
        current["tasks"][0].update(queue="q17 delivered", review="accepted", checks="unit: pass", delivery="merged abc", cleanup="pending")
        current["tasks"][0]["native"]["state"] = "done"
        state = json.loads(ET.fromstring(dash.render(self.snapshot)).find("state").text)
        ops = json.loads(dash.patch(self.snapshot, current))
        self.assertEqual(ops[0], {"op": "test", "path": "/revision", "value": 1})
        for op in ops:
            key = op["path"][1:]
            if op["op"] == "test":
                actual = state["board"]["run"] if key == "board/run" else state[key]
                self.assertEqual(actual, op["value"])
            else:
                self.assertEqual(op["op"], "replace")
                state[key] = op["value"]
        expected = json.loads(ET.fromstring(dash.render(current)).find("state").text)
        self.assertEqual(state, expected)
        self.assertNotIn("show", dash.patch(self.snapshot, current))
        for bad in (self.snapshot, {**current, "run": "another"}):
            with self.assertRaises(ValueError):
                dash.patch(self.snapshot, bad)

    def test_native_size_limits(self):
        current = copy.deepcopy(self.snapshot)
        current["revision"] += 1
        current["tasks"][0]["checks"] = "x" * (64 * 1024)
        with self.assertRaisesRegex(ValueError, "64 KiB"):
            dash.patch(self.snapshot, current)
        current["tasks"][0]["checks"] *= 4
        with self.assertRaisesRegex(ValueError, "256 KiB"):
            dash.render(current)

    def test_cli_error_and_duplicate_json_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"run":"one","run":"two"}')
            result = subprocess.run([sys.executable, str(ROOT / "scripts/dashboard.py"), "render", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertIn("duplicate JSON key", result.stderr)


if __name__ == "__main__":
    unittest.main()
