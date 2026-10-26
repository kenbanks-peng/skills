"""Saved UI identity cleanup, including lost responses and foreign panes."""

import copy
import json
import os
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dispatch_lib import cleanup_ui as ui


class CleanupUITests(unittest.TestCase):
    def setUp(self):
        self.context = {"backend": "herdr", "instance": "/original/herdr.sock"}
        self.agent = {"pane_id": "boot~terminal", "window_name": "not-an-identity"}
        self.item = {}
        self.saved = []
        self.pane = {
            "pane_id": "native",
            "terminal_id": "terminal",
            "tab_id": "tab",
            "workspace_id": "workspace",
            "cwd": "/worker",
        }
        self.foreign = dict(
            self.pane,
            pane_id="foreign",
            terminal_id="foreign-term",
            tab_id="other-tab",
            cwd="/elsewhere",
        )
        self.inventory = {
            "panes": [self.pane, self.foreign],
            "tabs": [
                {"tab_id": "tab", "workspace_id": "workspace"},
                {"tab_id": "other-tab", "workspace_id": "workspace"},
            ],
        }
        self.closed = {"panes": [self.foreign], "tabs": [self.inventory["tabs"][1]]}
        self.patcher = patch.object(ui, "SavedHerdr")
        self.factory = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.client = self.factory.return_value

    def persist(self):
        self.saved.append(copy.deepcopy(self.item))

    def close(self):
        ui.close_worker_ui(self.context, self.agent, "/worker", self.item, self.persist)

    def test_exact_terminal_closes_its_tab_only_and_persists_intent(self):
        self.client.snapshot.side_effect = [self.inventory, self.inventory, self.closed]
        self.close()
        self.factory.assert_called_once_with("/original/herdr.sock", "boot")
        self.client.request.assert_called_once_with("tab.close", tab_id="tab")
        self.assertEqual(
            self.saved[-1]["target"],
            {
                "pane_id": "native",
                "terminal_id": "terminal",
                "tab_id": "tab",
                "workspace_id": "workspace",
            },
        )
        self.assertTrue(self.saved[-1]["close_attempted"])

    def test_identity_mismatch_never_closes(self):
        for field, value in (("cwd", "/other"), ("terminal_id", "replacement")):
            with self.subTest(field=field):
                inventory = copy.deepcopy(self.inventory)
                inventory["panes"][0][field] = value
                self.client.snapshot.side_effect = None
                self.client.snapshot.return_value = inventory
                with self.assertRaises(ValueError):
                    self.close()
                self.client.request.assert_not_called()

    def test_shared_tab_is_preserved(self):
        inventory = copy.deepcopy(self.inventory)
        inventory["panes"][1]["tab_id"] = "tab"
        self.client.snapshot.return_value = inventory
        with self.assertRaisesRegex(ValueError, "other panes"):
            self.close()
        self.client.request.assert_not_called()

    def test_pane_moved_between_snapshots_is_preserved(self):
        moved = copy.deepcopy(self.inventory)
        moved["panes"][0]["pane_id"] = "moved"
        self.client.snapshot.side_effect = [self.inventory, moved]
        with self.assertRaisesRegex(ValueError, "changed before"):
            self.close()
        self.client.request.assert_not_called()

    def test_lost_close_response_reconciles_without_duplicate_mutation(self):
        self.client.snapshot.side_effect = [self.inventory, self.inventory]
        self.client.request.side_effect = OSError("lost reply")
        with self.assertRaises(OSError):
            self.close()
        self.client.snapshot.side_effect = [self.closed]
        self.close()
        self.assertEqual(self.client.request.call_count, 1)

    def test_failed_close_retries_only_same_target(self):
        self.client.snapshot.side_effect = [self.inventory, self.inventory]
        self.client.request.side_effect = OSError("unavailable")
        with self.assertRaises(OSError):
            self.close()
        self.client.request.side_effect = None
        self.client.snapshot.side_effect = [self.inventory, self.inventory, self.closed]
        self.close()
        self.assertEqual(self.client.request.call_count, 2)

    def test_absent_terminal_without_saved_close_intent_is_not_success(self):
        self.client.snapshot.return_value = self.closed
        with self.assertRaisesRegex(ValueError, "missing"):
            self.close()
        self.client.request.assert_not_called()

    def test_native_unqualified_pane_is_not_a_workmux_identity(self):
        self.agent["pane_id"] = "native"
        with self.assertRaisesRegex(ValueError, "lifetime-qualified"):
            self.close()
        self.factory.assert_not_called()

    def test_tmux_is_pinned_to_original_socket_and_verified(self):
        context = {"backend": "tmux", "socket_path": "/original.sock"}
        agent = {"pane_id": "%1", "session": "$1"}
        with patch.object(
            ui,
            "run",
            side_effect=[
                "/original.sock\t%1\t$1\t/worker",
                "",
                "%2\n",
            ],
        ) as command:
            ui.close_worker_ui(context, agent, "/worker", self.item, self.persist)
        self.assertTrue(
            all(
                call.args[0][:3] == ["tmux", "-S", "/original.sock"]
                for call in command.call_args_list
            )
        )
        self.assertTrue(self.item["close_attempted"])
        with patch.object(ui, "run", return_value="%2\n") as command:
            ui.close_worker_ui(context, agent, "/worker", self.item, self.persist)
        self.assertEqual(command.call_count, 1)


@unittest.skipUnless(sys.platform == "linux", "Linux kernel peer credential contract")
class PeerTransportTests(unittest.TestCase):
    def test_server_lifetime_is_checked_before_request_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            endpoint = str(Path(directory) / "herdr.sock")
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(endpoint)
                server.listen()
                received = []

                def serve():
                    with server.accept()[0] as stream:
                        with stream.makefile("rb") as reader:
                            data = reader.readline()
                        received.append(data)
                        if data:
                            request = json.loads(data)
                            stream.sendall(
                                json.dumps({"id": request["id"], "result": {}}).encode()
                                + b"\n"
                            )

                thread = threading.Thread(target=serve)
                thread.start()
                client = ui.SavedHerdr(endpoint, "wrong-server-lifetime")
                with self.assertRaisesRegex(ValueError, "lifetime changed"):
                    client.request("tab.close", tab_id="unrelated")
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                self.assertEqual(received, [b""])
                self.assertEqual(os.stat(endpoint).st_ino, client.identity[1])
