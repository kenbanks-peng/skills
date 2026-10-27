"""Opt-in native daemon smoke test, not Linux or live-agent acceptance.

Run: DISPATCH_NATIVE_TEST=1 python3 -m unittest discover -s tests -p test_native.py -v
Creates and removes its own server and scratch repository. Never restarts the
shared daemon or uses a production worktree.
"""
import copy
import json
import os
import platform
from pathlib import Path
import secrets
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.environ.get("DISPATCH_NATIVE_TEST") == "1", "opt-in native smoke")
class NativeSmokeTests(unittest.TestCase):
    def test_scripted_lifecycle(self):
        server = "dsp-a-" + secrets.token_hex(3)
        env = {**os.environ, "TUIOS_SERVER": server}

        def command(*argv, cwd=None):
            result = subprocess.run(list(argv), cwd=cwd, env=env, text=True,
                                    capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0,
                             f"{argv}: {result.stdout}\\n{result.stderr}")
            return result.stdout

        def tuios(*args):
            return command("tuios", "--server", server, *args)

        def script(name, *args):
            return command("python3", str(ROOT / "scripts" / name), *map(str, args))

        with tempfile.TemporaryDirectory(prefix="dispatch-automation-") as directory:
            base = Path(directory)
            repo = base / "repo"
            repo.mkdir()
            command("git", "init", "-b", "main", str(repo))
            command("git", "config", "user.name", "Dispatch Test", cwd=repo)
            command("git", "config", "user.email", "test@example.invalid", cwd=repo)
            command("git", "config", "commit.gpgsign", "false", cwd=repo)
            (repo / "seed").write_text("seed\\n")
            command("git", "add", ".", cwd=repo)
            command("git", "commit", "-m", "seed", cwd=repo)
            try:
                # These fixture panes use an isolated daemon with no attached client.
                tuios("new", "dispatch", "--detach", "--cwd", str(repo))
                windows = json.loads(tuios("list-windows", "-s", "dispatch", "--json"))
                dispatch = windows["windows"][0]["window_id"]
                run = base / "run"
                script("workspace.py", "--run-dir", run, "init", "--repo", repo,
                       "--session", "dispatch", "--dispatch", dispatch)
                tuios("worktree", "new", "automation-change", "--repo", str(repo),
                      "--base", "main", "--name", "worker", "--detach", "--json")
                inventory = json.loads(tuios("ls", "--json"))
                worker = next(row for row in inventory if row["name"] == "worker")
                source = Path(worker["worktree"]["path"])
                window = worker["windows"][0]["id"]
                script("workspace.py", "--run-dir", run, "register", "--session",
                       "worker", "--window", window, "--role", "auxiliary")
                (source / "result").write_text("reviewed result\\n")
                plan = base / "plan.json"
                plan.write_text(json.dumps([{
                    "name": "diff", "argv": ["git", "--no-pager", "diff", "--check"],
                    "timeout_s": 10}]))
                script("checks.py", "--plan", plan, "--cwd", source,
                       "--output", base / "checks", "--require-system", platform.system())
                script("deliver.py", "--run-dir", run, "--session", "worker",
                       "--window", window, "--cwd", source, "--target-repo", repo,
                       "--into", "main", "--policy", "squash", "--message", "Integrate",
                       "--checks", base / "checks/result.json", "--integration-plan", plan,
                       "--output", base / "delivery", "--reviewed")
                result = json.loads((base / "delivery/result.json").read_text())
                self.assertEqual(result["status"], "delivered")
                self.assertEqual((repo / "result").read_text(), "reviewed result\\n")
                script("workspace.py", "--run-dir", run, "cleanup", "--evidence-saved")
                script("workspace.py", "--run-dir", run, "audit", "--final")
                remaining = json.loads(tuios("list-windows", "--all", "--all-hosts", "--json"))
                self.assertEqual([row["window_id"] for row in remaining["panes"]], [dispatch])
                tuios("worktree", "rm", "worker", "--json")
            finally:
                subprocess.run(["tuios", "--server", server, "kill-server"],
                               env=env, capture_output=True, timeout=15)

    def test_dashboard_checks_ship_and_cleanup(self):
        server = "dsp-" + secrets.token_hex(3)
        env = os.environ.copy()
        # Use the documented named server route; preserve caller credentials.
        env["TUIOS_SERVER"] = server

        def command(argv, cwd=None, expected=0):
            result = subprocess.run(argv, cwd=cwd, env=env, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    timeout=30)
            self.assertEqual(result.returncode, expected,
                             f"{argv}: {result.stdout}\n{result.stderr}")
            return result.stdout

        def tuios(*args, expected=0):
            return command(["tuios", "--server", server, *args], expected=expected)

        with tempfile.TemporaryDirectory(prefix="dispatch-native-") as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            command(["git", "init", "-b", "main", str(repo)])
            command(["git", "config", "user.name", "Dispatch Test"], cwd=repo)
            command(["git", "config", "user.email", "dispatch-test@example.invalid"], cwd=repo)
            (repo / "seed.txt").write_text("seed\n")
            command(["git", "add", "seed.txt"], cwd=repo)
            command(["git", "commit", "-m", "Seed native test"], cwd=repo)
            try:
                tuios("new", "status", "--detach", "--cwd", str(repo))
                snapshot = json.loads((ROOT / "assets/dashboard-example.json").read_text())
                snapshot.update(run="native-smoke", observed_at="native test")
                source = Path(directory) / "snapshot.json"
                document = Path(directory) / "dashboard.tml"
                source.write_text(json.dumps(snapshot))
                document.write_text(command(["python3", str(ROOT / "scripts/dashboard.py"),
                                             "render", str(source)]))
                tuios("tml", "validate", str(document))
                rendered = tuios("tml", "render", str(document), "--width", "80", "--height", "24")
                self.assertIn("TASK-1", rendered)
                opened = json.loads(tuios("tml", "show", str(document), "--pane",
                                         "-s", "status", "--json"))
                surface, pane = opened["surface"], opened["window_id"]
                self.assertIn("TASK-1", tuios("capture-pane", "-s", "status", "-w", pane))
                before = json.loads(tuios("tml", "get", surface))
                current = copy.deepcopy(snapshot)
                current["revision"] += 1
                current["tasks"][0]["native"]["state"] = "done"
                following = Path(directory) / "next.json"
                following.write_text(json.dumps(current))
                patch = command(["python3", str(ROOT / "scripts/dashboard.py"), "patch",
                                 str(source), str(following)])
                tuios("tml", "patch", surface, patch)
                after = json.loads(tuios("tml", "get", surface))
                self.assertEqual(before["surface"], after["surface"])
                self.assertEqual(after["state"]["revision"], current["revision"])
                self.assertIn("done", tuios("capture-pane", "-s", "status", "-w", pane))
                tuios("tml", "patch", surface, patch, expected=1)

                tuios("worktree", "new", "native-change", "--repo", str(repo),
                      "--base", "main", "--name", "worker", "--detach", "--json")
                inventory = json.loads(tuios("ls", "--json"))
                worker = next(row for row in inventory if row["name"] == "worker")
                worktree = Path(worker["worktree"]["path"])
                starter = worker["windows"][0]["id"]
                (worktree / "result.txt").write_text("native result\n")

                for exit_code in (0, 7):
                    # A failed command is captured and closed just like a pass.
                    tuios("new-window", "-s", "worker", "checks", "--cwd", str(worktree),
                          "--no-focus", "--keep-open", "--wait", "--", "sh", "-c",
                          f"export GIT_PAGER=cat PAGER=cat; git --no-pager diff --check; echo CHECK-{exit_code}; exit {exit_code}",
                          expected=exit_code)
                    log = tuios("capture-pane", "-s", "worker", "-w", "checks",
                                "--scrollback", "--lines", "0")
                    self.assertIn(f"CHECK-{exit_code}", log)
                    tuios("close-window", "-s", "worker", "checks")
                    panes = json.loads(tuios("list-windows", "-s", "worker", "--json"))
                    self.assertEqual(len(panes["windows"]), 1)

                # A native view shows the source pane without relocating its agent.
                source_pane = json.loads(tuios(
                    "new-window", "-s", "worker", "view-source", "--no-focus",
                    "--keep-open", "--json", "--", "sh", "-c",
                    "echo NATIVE_VIEW_READY; sleep 3"))["window_id"]
                tuios("wait-for", "window-output", "-s", "worker", "-w", source_pane,
                      "--pattern", "NATIVE_VIEW_READY", "--timeout", "10000")
                view = json.loads(tuios(
                    "new-window", "-s", "status", "worker-view", "--no-focus",
                    "--json", "--", "tuios", "--server", server, "pane-view",
                    "-s", "worker", "-w", source_pane, "--size", "pane"))["window_id"]
                tuios("wait-for", "window-output", "-s", "status", "-w", view,
                      "--pattern", "NATIVE_VIEW_READY", "--timeout", "10000")
                self.assertIn("NATIVE_VIEW_READY", tuios(
                    "capture-pane", "-s", "status", "-w", view))
                tuios("close-window", "-s", "status", view)
                # Closing a view must leave the actual worker pane intact.
                tuios("get-window", source_pane, "-s", "worker", "--json")
                tuios("close-window", "-s", "worker", source_pane)

                tuios("ship", "commit", "-s", "worker", "-w", starter,
                      "-m", "Native change")
                tuios("ship", "merge", "-s", "worker", "-w", starter,
                      "--into", "main", "--squash", "-m", "Integrate native change")
                self.assertEqual((repo / "result.txt").read_text(), "native result\n")
                self.assertEqual(command(["git", "status", "--porcelain"], cwd=repo), "")
                tuios("worktree", "rm", "worker", "--json")
                self.assertFalse(worktree.exists())
                tuios("tml", "close", surface, '"done"')
                tuios("kill-session", "status")
                self.assertEqual(json.loads(tuios("ls", "--json")), [])
            finally:
                # Only this randomly named server belongs to the test.
                subprocess.run(["tuios", "--server", server, "kill-server"],
                               env=env, capture_output=True, timeout=15)


if __name__ == "__main__":
    unittest.main()
