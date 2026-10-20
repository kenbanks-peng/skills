"""Exact dispatcher identity, explicit startup and idempotent naming contracts."""

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dispatch_ui.py"
SPEC = importlib.util.spec_from_file_location("dispatch_ui", SCRIPT)
ui = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ui)


class DispatchUITests(unittest.TestCase):
    def setUp(self):
        self.inventory = {
            "version": "0.9.0", "protocol": 22,
            "focused_tab_id": "unrelated",
            "panes": [
                {"pane_id": "worker", "terminal_id": "term-1",
                 "tab_id": "unrelated", "workspace_id": "w"},
                {"pane_id": "actual", "terminal_id": "term-2",
                 "tab_id": "target", "workspace_id": "w"},
            ],
            "tabs": [
                {"tab_id": "unrelated", "workspace_id": "w", "label": "dispatcher"},
                {"tab_id": "target", "workspace_id": "w", "label": "old"},
            ],
        }
        self.calls = []
        self.pids = {"worker": 999999, "actual": 42}
        self.env = {"HERDR_ENV": "1", "HERDR_SOCKET_PATH": "/host/herdr.sock",
                    "HERDR_ACTIVE_PANE_ID": "worker"}

    def request(self, method, **params):
        self.calls.append((method, params))
        if method == "session.snapshot":
            return {"snapshot": self.inventory}
        if method == "pane.process_info":
            return {"process_info": {"shell_pid": self.pids[params["pane_id"]]}}
        if method == "tab.rename":
            self.assertEqual(params, {"tab_id": "target", "label": "dispatcher"})
            self.inventory["tabs"][1]["label"] = params["label"]
            return {}
        self.fail(method)

    def start(self):
        with patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)), \
             patch.object(ui.Herdr, "request", side_effect=self.request), \
             patch.object(ui, "ancestors", return_value={42, 43}):
            return ui.startup(self.env)

    def assert_no_rename(self):
        self.assertNotIn("tab.rename", [method for method, _ in self.calls])

    def test_exact_ancestry_not_focus_label_or_inherited_hint_and_repeat(self):
        self.assertEqual(self.start(), {"backend": "herdr", "pane_id": "actual",
                                       "tab_id": "target", "name": "dispatcher"})
        self.start()
        self.assertEqual([params for method, params in self.calls if method == "tab.rename"],
                         [{"tab_id": "target", "label": "dispatcher"}])
        self.assertEqual(self.inventory["tabs"][0]["label"], "dispatcher")

    def test_missing_or_ambiguous_ancestry_refuses_before_mutation(self):
        for pids, count in [({"worker": 900, "actual": 901}, 0),
                            ({"worker": 42, "actual": 43}, 2)]:
            with self.subTest(count=count):
                self.pids = pids
                with self.assertRaisesRegex(ui.UIError, f"{count} ancestry matches"):
                    self.start()
                self.assert_no_rename()

    def test_missing_or_ambiguous_tab_refuses(self):
        for tabs in [[], [self.inventory["tabs"][1]] * 2]:
            with self.subTest(tabs=tabs):
                self.inventory["tabs"] = tabs
                with self.assertRaisesRegex(ui.UIError, "ambiguous Herdr tab"):
                    self.start()
                self.assert_no_rename()

    def test_wrong_workspace_refuses(self):
        self.inventory["tabs"][1]["workspace_id"] = "other"
        with self.assertRaisesRegex(ui.UIError, "tab identity"):
            self.start()
        self.assert_no_rename()

    def test_unsupported_protocol_refuses(self):
        self.inventory["protocol"] = 21
        with self.assertRaisesRegex(ui.UIError, "Unsupported Herdr"):
            self.start()
        self.assert_no_rename()

    def test_moved_pane_refuses_old_tab(self):
        original = self.request
        snapshots = 0

        def moved(method, **params):
            nonlocal snapshots
            if method == "session.snapshot":
                snapshots += 1
                if snapshots == 2:
                    # Replace, rather than mutate the saved first snapshot's row.
                    self.inventory["panes"][1] = dict(self.inventory["panes"][1],
                                                      tab_id="unrelated")
            return original(method, **params)

        with patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)), \
             patch.object(ui.Herdr, "request", side_effect=moved), \
             patch.object(ui, "ancestors", return_value={42}):
            with self.assertRaisesRegex(ui.UIError, "moved"):
                ui.startup(self.env)
        self.assert_no_rename()

    def test_missing_context_or_socket_has_clear_diagnostic(self):
        for env, diagnostic in [({}, "original Herdr or tmux"),
                                ({"HERDR_ENV": "1"}, "HERDR_SOCKET_PATH"),
                                ({"HERDR_ENV": "1", "HERDR_SOCKET_PATH": "relative"},
                                 "HERDR_SOCKET_PATH")]:
            with self.subTest(env=env), self.assertRaisesRegex(ui.UIError, diagnostic):
                ui.startup(env)

    def test_tmux_uses_exact_pane_and_window_on_repeat(self):
        calls = []

        def command(argv):
            calls.append(argv)
            if argv[-1] == "#{pane_id}\t#{window_id}":
                return "%17\t@31"
            if argv[-1] == "#{window_id}\t#{window_name}":
                return "@31\tdispatcher"
            return ""

        with patch.object(ui, "command", side_effect=command):
            for _ in range(2):
                self.assertEqual(ui.startup({"TMUX": "socket", "TMUX_PANE": "%17"})["tab_id"],
                                 "@31")
        mutations = [argv for argv in calls if argv[1] != "display-message"]
        self.assertEqual(mutations, [
            ["tmux", "set-window-option", "-t", "@31", "automatic-rename", "off"],
            ["tmux", "rename-window", "-t", "@31", "dispatcher"],
        ] * 2)

    def test_tmux_missing_or_mismatched_identity_never_renames(self):
        with patch.object(ui, "command", return_value="%99\t@31") as command:
            for pane in ["", "guessed-label", "%17"]:
                with self.subTest(pane=pane), self.assertRaises(ui.UIError):
                    ui.startup({"TMUX": "socket", "TMUX_PANE": pane})
            self.assertEqual(command.call_count, 1)

    def test_help_and_invalid_actions_cannot_mutate(self):
        for action, code in [("--help", 0), ("intake", 2), ("finish", 2)]:
            result = subprocess.run([sys.executable, str(SCRIPT), action],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, code)

    def test_real_host_ancestry_contains_this_process(self):
        self.assertIn(os.getpid(), ui.ancestors())


class WorkerTabTests(unittest.TestCase):
    def setUp(self):
        self.ui = {"context": {"backend": "herdr", "instance": "/host/api.sock"},
                   "agents": [{"pane_id": "boot~terminal", "session": "session"}]}
        self.pane = dict(pane_id="native", terminal_id="terminal", tab_id="target",
                         workspace_id="ws")
        self.tab = dict(tab_id="target", workspace_id="ws", label="old")
        self.other = dict(tab_id="unrelated", workspace_id="ws", label="Dme-XaPY")
        self.calls = []
        self.snapshots = 0
        self.move_at = None

    def request(self, method, **params):
        self.calls.append((method, params))
        if method == "session.snapshot":
            self.snapshots += 1
            if self.snapshots == self.move_at:
                self.pane["tab_id"] = "unrelated"
            return {"snapshot": dict(version="0.9.0", protocol=22,
                                     panes=[dict(self.pane)], tabs=[self.tab, self.other])}
        self.assertEqual(method, "tab.rename")
        self.assertEqual(params, {"tab_id": "target", "label": "Dme-XaPY"})
        self.tab["label"] = params["label"]
        return {}

    def name(self, saved=None, rename=True):
        with patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)), \
             patch.object(ui.Herdr, "request", side_effect=self.request):
            return ui.worker_tab(self.ui, "Dme-XaPY", saved, rename=rename)

    def test_exact_case_no_decoration_and_idempotence(self):
        saved = self.name(rename=False)
        self.assertFalse(any(m == "tab.rename" for m, _ in self.calls))
        for status in ("working", "waiting", "done"):
            self.ui["agents"][0]["status"] = status
            self.assertEqual(self.name(saved), saved)
            self.assertEqual(self.tab["label"], "Dme-XaPY")
        self.assertEqual(sum(m == "tab.rename" for m, _ in self.calls), 1)
        self.assertEqual(self.other["label"], "Dme-XaPY")

    def test_saved_identity_rejects_moved_pane_or_replaced_socket(self):
        saved = self.name(rename=False)
        for key, value in (("tab_id", "unrelated"), ("workspace_id", "other"),
                           ("socket_identity", [9, 9]), ("workmux_pane", "new~terminal")):
            with self.subTest(key=key), self.assertRaisesRegex(ui.UIError, "identity changed"):
                self.name(dict(saved, **{key: value}))
        self.assertFalse(any(m == "tab.rename" for m, _ in self.calls))

    def test_move_between_resolution_and_mutation_refuses(self):
        self.move_at = 2
        with self.assertRaisesRegex(ui.UIError, "moved"):
            self.name()
        self.assertFalse(any(m == "tab.rename" for m, _ in self.calls))

    def test_missing_terminal_never_uses_matching_label(self):
        self.ui["agents"][0]["pane_id"] = "boot~missing"
        with self.assertRaisesRegex(ui.UIError, "terminal identity"):
            self.name()
        self.assertFalse(any(m == "tab.rename" for m, _ in self.calls))

    def test_tmux_uses_saved_socket_pane_session_and_window(self):
        self.ui = {"context": {"backend": "tmux", "instance": "/host/tmux.sock"},
                   "agents": [{"pane_id": "%17", "session": "$3"}]}
        calls = []

        def command(argv):
            calls.append(argv)
            self.assertEqual(argv[:3], ["tmux", "-S", "/host/tmux.sock"])
            if argv[-1] == "#{pane_id}\t#{window_id}\t#{session_id}":
                return "%17\t@31\t$3"
            if argv[-1] == "#{window_name}":
                return "Dme-XaPY"
            return ""

        with patch.object(ui, "command", side_effect=command):
            saved = ui.worker_tab(self.ui, "Dme-XaPY", rename=False)
            ui.worker_tab(self.ui, "Dme-XaPY", saved)
            with self.assertRaisesRegex(ui.UIError, "identity changed"):
                ui.worker_tab(self.ui, "Dme-XaPY", dict(saved, tab_id="@99"))
        mutations = [argv[3:] for argv in calls if argv[3] != "display-message"]
        self.assertEqual(mutations, [
            ["set-window-option", "-t", "@31", "automatic-rename", "off"],
            ["set-window-option", "-t", "@31", "allow-rename", "off"],
            ["rename-window", "-t", "@31", "Dme-XaPY"],
        ])


class SocketContractTests(unittest.TestCase):
    def test_line_protocol_and_api_error(self):
        for error in [False, True]:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory:
                endpoint = str(Path(directory) / "api.sock")
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                    server.bind(endpoint)
                    server.listen()
                    received = []

                    def respond():
                        stream, _ = server.accept()
                        with stream, stream.makefile("rb") as incoming:
                            received.append(json.loads(incoming.readline()))
                            data = {"id": "dispatch-ui"}
                            data.update({"error": {"code": "denied"}} if error else
                                        {"result": {"ok": True}})
                            stream.sendall(json.dumps(data).encode() + b"\n")

                    thread = threading.Thread(target=respond, daemon=True)
                    thread.start()
                    client = ui.Herdr(endpoint)
                    if error:
                        with self.assertRaisesRegex(ui.UIError, "denied"):
                            client.request("tab.rename", tab_id="exact", label="dispatcher")
                    else:
                        self.assertEqual(client.request("tab.rename", tab_id="exact",
                                                        label="dispatcher"), {"ok": True})
                    thread.join(timeout=5)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual(received, [{"id": "dispatch-ui", "method": "tab.rename",
                                                "params": {"tab_id": "exact",
                                                           "label": "dispatcher"}}])

    def test_replaced_socket_is_not_reused(self):
        with patch.object(ui.Herdr, "socket_identity", side_effect=[(1, 2), (1, 3)]):
            client = ui.Herdr("/host/api.sock")
            with self.assertRaisesRegex(ui.UIError, "socket changed"):
                client.request("tab.rename", tab_id="old", label="dispatcher")


if __name__ == "__main__":
    unittest.main()
