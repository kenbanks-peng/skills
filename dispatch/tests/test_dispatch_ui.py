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
            "version": "0.9.0",
            "protocol": 22,
            "focused_tab_id": "unrelated",
            "panes": [
                {
                    "pane_id": "worker",
                    "terminal_id": "term-1",
                    "tab_id": "unrelated",
                    "workspace_id": "w",
                },
                {
                    "pane_id": "actual",
                    "terminal_id": "term-2",
                    "tab_id": "target",
                    "workspace_id": "w",
                },
            ],
            "tabs": [
                {"tab_id": "unrelated", "workspace_id": "w", "label": "dispatcher"},
                {"tab_id": "target", "workspace_id": "w", "label": "old"},
            ],
        }
        self.calls = []
        self.pids = {"worker": 999999, "actual": 42}
        self.env = {
            "HERDR_ENV": "1",
            "HERDR_SOCKET_PATH": "/host/herdr.sock",
            "HERDR_ACTIVE_PANE_ID": "worker",
        }

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
        with (
            patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)),
            patch.object(ui.Herdr, "request", side_effect=self.request),
            patch.object(ui, "ancestors", return_value={42, 43}),
        ):
            return ui.startup(self.env)

    def assert_no_rename(self):
        self.assertNotIn("tab.rename", [method for method, _ in self.calls])

    def test_exact_ancestry_not_focus_label_or_inherited_hint_and_repeat(self):
        self.assertEqual(
            self.start(),
            {
                "backend": "herdr",
                "pane_id": "actual",
                "tab_id": "target",
                "name": "dispatcher",
            },
        )
        self.start()
        self.assertEqual(
            [params for method, params in self.calls if method == "tab.rename"],
            [{"tab_id": "target", "label": "dispatcher"}],
        )
        self.assertEqual(self.inventory["tabs"][0]["label"], "dispatcher")

    def test_missing_or_ambiguous_ancestry_refuses_before_mutation(self):
        for pids, count in [
            ({"worker": 900, "actual": 901}, 0),
            ({"worker": 42, "actual": 43}, 2),
        ]:
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
                    self.inventory["panes"][1] = dict(
                        self.inventory["panes"][1], tab_id="unrelated"
                    )
            return original(method, **params)

        with (
            patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)),
            patch.object(ui.Herdr, "request", side_effect=moved),
            patch.object(ui, "ancestors", return_value={42}),
        ):
            with self.assertRaisesRegex(ui.UIError, "moved"):
                ui.startup(self.env)
        self.assert_no_rename()

    def test_missing_context_or_socket_has_clear_diagnostic(self):
        for env, diagnostic in [
            ({}, "original Herdr or tmux"),
            ({"HERDR_ENV": "1"}, "HERDR_SOCKET_PATH"),
            ({"HERDR_ENV": "1", "HERDR_SOCKET_PATH": "relative"}, "HERDR_SOCKET_PATH"),
        ]:
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
                self.assertEqual(
                    ui.startup({"TMUX": "socket", "TMUX_PANE": "%17"})["tab_id"], "@31"
                )
        mutations = [argv for argv in calls if argv[1] != "display-message"]
        self.assertEqual(
            mutations,
            [
                ["tmux", "set-window-option", "-t", "@31", "automatic-rename", "off"],
                ["tmux", "rename-window", "-t", "@31", "dispatcher"],
            ]
            * 2,
        )

    def test_tmux_missing_or_mismatched_identity_never_renames(self):
        with patch.object(ui, "command", return_value="%99\t@31") as command:
            for pane in ["", "guessed-label", "%17"]:
                with self.subTest(pane=pane), self.assertRaises(ui.UIError):
                    ui.startup({"TMUX": "socket", "TMUX_PANE": pane})
            self.assertEqual(command.call_count, 1)

    def test_help_and_invalid_actions_cannot_mutate(self):
        for action, code in [("--help", 0), ("intake", 2), ("finish", 2)]:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), action], capture_output=True, text=True
            )
            self.assertEqual(result.returncode, code)

    def test_real_host_ancestry_contains_this_process(self):
        self.assertIn(os.getpid(), ui.ancestors())


class WorkerTabTests(unittest.TestCase):
    def setUp(self):
        self.ui = {
            "context": {"backend": "herdr", "instance": "/host/api.sock"},
            "agents": [{"pane_id": "boot~terminal", "session": "session"}],
        }
        self.pane = dict(
            pane_id="native", terminal_id="terminal", tab_id="target", workspace_id="ws"
        )
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
            return {
                "snapshot": dict(
                    version="0.9.0",
                    protocol=22,
                    panes=[dict(self.pane)],
                    tabs=[self.tab, self.other],
                )
            }
        self.assertEqual(method, "tab.rename")
        self.assertEqual(params, {"tab_id": "target", "label": "Dme-XaPY"})
        self.tab["label"] = params["label"]
        return {}

    def name(self, saved=None):
        with (
            patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)),
            patch.object(ui.Herdr, "request", side_effect=self.request),
        ):
            return ui.worker_tab(self.ui, saved)

    def test_identity_and_existing_label_are_preserved(self):
        saved = self.name()
        self.assertEqual(saved["tab_id"], "target")
        for status in ("working", "waiting", "done"):
            self.ui["agents"][0]["status"] = status
            self.assertEqual(self.name(saved), saved)
            self.assertEqual(self.tab["label"], "old")

    def test_saved_identity_rejects_moved_pane_or_replaced_socket(self):
        saved = self.name()
        for key, value in (
            ("tab_id", "unrelated"),
            ("workspace_id", "other"),
            ("socket_identity", [9, 9]),
            ("workmux_pane", "new~terminal"),
        ):
            with (
                self.subTest(key=key),
                self.assertRaisesRegex(ui.UIError, "identity changed"),
            ):
                self.name(dict(saved, **{key: value}))
        self.assertFalse(any(m == "tab.rename" for m, _ in self.calls))

    def test_missing_terminal_never_uses_matching_label(self):
        self.ui["agents"][0]["pane_id"] = "boot~missing"
        with self.assertRaisesRegex(ui.UIError, "terminal identity"):
            self.name()
        self.assertFalse(any(m == "tab.rename" for m, _ in self.calls))

    def test_tmux_uses_saved_socket_pane_session_and_window(self):
        self.ui = {
            "context": {"backend": "tmux", "instance": "/host/tmux.sock"},
            "agents": [{"pane_id": "%17", "session": "$3"}],
        }
        calls = []
        label = "old-name"

        def command(argv):
            nonlocal label
            calls.append(argv)
            self.assertEqual(argv[:3], ["tmux", "-S", "/host/tmux.sock"])
            if argv[3] == "rename-window":
                label = argv[-1]
            if argv[-1] == "#{pane_id}\t#{window_id}\t#{session_id}":
                return "%17\t@31\t$3"
            if argv[-1] == "#{window_name}":
                return label
            return ""

        with patch.object(ui, "command", side_effect=command):
            saved = ui.worker_tab(self.ui)
            ui.worker_tab(self.ui, saved)
            with self.assertRaisesRegex(ui.UIError, "identity changed"):
                ui.worker_tab(self.ui, dict(saved, tab_id="@99"))
        self.assertEqual(
            saved,
            dict(
                backend="tmux",
                endpoint="/host/tmux.sock",
                pane_id="%17",
                tab_id="@31",
                session="$3",
            ),
        )


class AvenTabTests(unittest.TestCase):
    def setUp(self):
        self.parent = dict(
            pane_id="dispatcher-pane",
            terminal_id="dispatcher-terminal",
            tab_id="dispatcher-tab",
            workspace_id="workspace",
        )
        self.aven = dict(
            pane_id="aven-pane",
            terminal_id="aven-terminal",
            tab_id="aven-tab",
            workspace_id="workspace",
        )
        self.inventory = dict(
            version="0.9.0",
            protocol=22,
            panes=[self.parent],
            tabs=[
                dict(self.parent, label="dispatcher"),
                dict(tab_id="unrelated", workspace_id="workspace", label="aven"),
            ],
        )
        self.calls = []
        self.saved = []
        self.record = {}
        self.env = dict(HERDR_ENV="1", HERDR_SOCKET_PATH="/host/api.sock")
        self.argv = ["/bin/aven", "tui", "--project", "dispatch"]

    def request(self, method, **params):
        self.calls.append((method, params))
        if method == "session.snapshot":
            return {"snapshot": self.inventory}
        if method == "pane.process_info":
            return {
                "process_info": {
                    "shell_pid": 42 if params["pane_id"] == "dispatcher-pane" else 900
                }
            }
        if method == "layout.apply":
            self.assertTrue(self.saved[-1]["creation_attempted"])
            self.assertNotIn("tab_id", params)
            self.inventory["panes"].append(self.aven)
            self.inventory["tabs"].append(dict(self.aven, label="aven"))
            return {"tab": {"tab_id": "aven-tab"}}
        if method == "tab.close":
            self.assertTrue(self.saved[-1]["aven_close_attempted"])
            self.inventory["panes"] = [
                p for p in self.inventory["panes"] if p["tab_id"] != params["tab_id"]
            ]
            self.inventory["tabs"] = [
                t for t in self.inventory["tabs"] if t["tab_id"] != params["tab_id"]
            ]
            return {}
        self.fail(method)

    def open(self):
        with (
            patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)),
            patch.object(ui.Herdr, "request", side_effect=self.request),
            patch.object(ui, "ancestors", return_value={42}),
            patch.object(ui, "startup"),
        ):
            return ui.aven_tab(
                "/target repo",
                self.argv,
                self.record,
                lambda data: self.saved.append(json.loads(json.dumps(data))),
                self.env,
            )

    def test_root_routing_and_exact_identity_repeat_ignores_labels(self):
        self.open()
        self.inventory["tabs"][-1]["label"] = "renamed by user"
        self.open()
        creates = [p for m, p in self.calls if m == "layout.apply"]
        self.assertEqual(
            creates,
            [
                dict(
                    workspace_id="workspace",
                    tab_label="aven",
                    focus=False,
                    root=dict(type="pane", cwd="/target repo", command=self.argv),
                )
            ],
        )
        self.assertEqual(self.record["aven_tab"], self.aven)
        self.assertEqual(self.record["dispatcher"]["tab_id"], "dispatcher-tab")
        self.assertFalse(any(m.endswith("close") for m, _ in self.calls))

    def test_missing_or_moved_saved_pane_never_creates_replacement(self):
        self.open()
        self.aven["tab_id"] = "unrelated"
        with self.assertRaisesRegex(ui.UIError, "identity changed"):
            self.open()
        self.assertEqual(sum(m == "layout.apply" for m, _ in self.calls), 1)

    def test_interrupted_creation_never_retries_by_label(self):
        self.record["creation_attempted"] = True
        with self.assertRaisesRegex(ui.UIError, "interrupted"):
            self.open()
        self.assertFalse(any(m == "layout.apply" for m, _ in self.calls))

    def test_replaced_socket_or_dispatcher_refuses(self):
        self.open()
        self.record["dispatcher"]["socket_identity"] = [9, 9]
        with self.assertRaisesRegex(ui.UIError, "dispatcher UI identity changed"):
            self.open()
        self.assertEqual(sum(m == "layout.apply" for m, _ in self.calls), 1)

    def test_tmux_creation_and_repeat_pin_server_session_window_and_pane(self):
        calls = []

        def command(argv):
            calls.append(argv)
            if argv[-1] == "#{socket_path}\t#{session_id}\t#{window_id}\t#{pane_id}":
                return "/host/tmux.sock\t$3\t@7\t%9"
            self.assertEqual(argv[:3], ["tmux", "-S", "/host/tmux.sock"])
            if argv[3] == "new-window":
                self.assertTrue(self.saved[-1]["creation_attempted"])
                return "@8\t%10"
            return "%10\t@8\t$3"

        with (
            patch.object(ui, "command", side_effect=command),
            patch.object(ui.os, "stat") as stat,
            patch.object(ui, "startup"),
        ):
            stat.return_value.st_dev = 1
            stat.return_value.st_ino = 2
            for _ in range(2):
                ui.aven_tab(
                    "/target repo",
                    self.argv,
                    self.record,
                    lambda data: self.saved.append(json.loads(json.dumps(data))),
                    {"TMUX": "context", "TMUX_PANE": "%9"},
                )
        creates = [c for c in calls if "new-window" in c]
        self.assertEqual(len(creates), 1)
        self.assertIn("$3:", creates[0])
        self.assertEqual(creates[0][-3:-1], ["-c", "/target repo"])
        self.assertIn("'/original tasks.db'", creates[0][-1])
        self.assertEqual(self.record["aven_tab"], dict(tab_id="@8", pane_id="%10"))

    def close(self):
        with (
            patch.object(ui.Herdr, "socket_identity", return_value=(1, 2)),
            patch.object(ui.Herdr, "request", side_effect=self.request),
            patch.object(ui.os, "stat") as stat,
        ):
            stat.return_value.st_dev = 1
            stat.return_value.st_ino = 2
            return ui.close_aven_tab(
                self.record,
                lambda data: self.saved.append(json.loads(json.dumps(data))),
            )

    def test_run_end_closes_only_saved_aven_tab_and_is_repeatable(self):
        self.open()
        self.close()
        self.close()
        self.assertTrue(self.record["aven_closed"])
        self.assertEqual(
            [p for m, p in self.calls if m == "tab.close"], [dict(tab_id="aven-tab")]
        )
        self.assertEqual(
            [t["tab_id"] for t in self.inventory["tabs"]],
            ["dispatcher-tab", "unrelated"],
        )

    def test_run_end_preserves_tab_with_extra_panes(self):
        self.open()
        self.inventory["panes"].append(
            dict(self.aven, pane_id="other", terminal_id="other-terminal")
        )
        with self.assertRaisesRegex(ui.UIError, "other panes"):
            self.close()
        self.assertFalse(any(m == "tab.close" for m, _ in self.calls))

    def test_run_end_refuses_changed_socket(self):
        self.open()
        self.record["dispatcher"]["socket_identity"] = [9, 9]
        with self.assertRaisesRegex(ui.UIError, "socket changed"):
            self.close()
        self.assertFalse(any(m == "tab.close" for m, _ in self.calls))

    def test_tmux_run_end_uses_saved_socket_and_preserves_other_windows(self):
        record = dict(
            dispatcher=dict(
                backend="tmux",
                endpoint="/host/tmux.sock",
                socket_identity=[1, 2],
                session="$3",
                tab_id="@7",
                pane_id="%9",
            ),
            aven_tab=dict(tab_id="@8", pane_id="%10"),
        )
        rows = ["%9\t@7\t$3", "%10\t@8\t$3", "%11\t@9\t$3"]
        calls = []

        def command(argv):
            calls.append(argv)
            self.assertEqual(argv[:3], ["tmux", "-S", "/host/tmux.sock"])
            if argv[3] == "kill-pane":
                self.assertTrue(record["aven_close_attempted"])
                self.assertEqual(argv[4:], ["-t", "%10"])
                rows.remove("%10\t@8\t$3")
                return ""
            return "\n".join(rows)

        with (
            patch.object(ui, "command", side_effect=command),
            patch.object(ui.os, "stat") as stat,
        ):
            stat.return_value.st_dev = 1
            stat.return_value.st_ino = 2
            rows.append("%12\t@8\t$3")
            with self.assertRaisesRegex(ui.UIError, "other panes"):
                ui.close_aven_tab(record, lambda data: None)
            rows.pop()
            ui.close_aven_tab(record, lambda data: None)
            ui.close_aven_tab(record, lambda data: None)
        self.assertEqual(rows, ["%9\t@7\t$3", "%11\t@9\t$3"])
        self.assertEqual(sum(c[3] == "kill-pane" for c in calls), 1)

    def test_legacy_close_cannot_close_run_or_worker_tabs(self):
        result = subprocess.run(
            ["bash", str(SCRIPT.with_name("close-tasks-tab.sh")), "herdr:aven-pane"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("run-owned", result.stderr)


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
                            data.update(
                                {"error": {"code": "denied"}}
                                if error
                                else {"result": {"ok": True}}
                            )
                            stream.sendall(json.dumps(data).encode() + b"\n")

                    thread = threading.Thread(target=respond, daemon=True)
                    thread.start()
                    client = ui.Herdr(endpoint)
                    if error:
                        with self.assertRaisesRegex(ui.UIError, "denied"):
                            client.request(
                                "tab.rename", tab_id="exact", label="dispatcher"
                            )
                    else:
                        self.assertEqual(
                            client.request(
                                "tab.rename", tab_id="exact", label="dispatcher"
                            ),
                            {"ok": True},
                        )
                    thread.join(timeout=5)
                    self.assertFalse(thread.is_alive())
                    self.assertEqual(
                        received,
                        [
                            {
                                "id": "dispatch-ui",
                                "method": "tab.rename",
                                "params": {"tab_id": "exact", "label": "dispatcher"},
                            }
                        ],
                    )

    def test_replaced_socket_is_not_reused(self):
        with patch.object(ui.Herdr, "socket_identity", side_effect=[(1, 2), (1, 3)]):
            client = ui.Herdr("/host/api.sock")
            with self.assertRaisesRegex(ui.UIError, "socket changed"):
                client.request("tab.rename", tab_id="old", label="dispatcher")


if __name__ == "__main__":
    unittest.main()
