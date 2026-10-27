"""Deterministic automation tests. Native calls use a strict fake, not a shared daemon."""
# ruff: noqa: E402 -- Load standalone script modules from their install directory.

import argparse
import copy
import platform
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import checks
import dashboard
import deliver
import runtime
import workspace

DISPATCH = "10000000-0000-0000-0000-000000000001"
WORKER = "10000000-0000-0000-0000-000000000002"
UNRELATED = "10000000-0000-0000-0000-000000000003"
UNKNOWN = "10000000-0000-0000-0000-000000000004"


def pane(window, session="dispatch", state="none", cwd=None):
    return {
        "window_id": window,
        "session": session,
        "host": "local",
        "name": window,
        "agent_state": state,
        "cwd": str(cwd or "/tmp"),
    }


def address(row):
    return row["session"] + "/" + row["window_id"]


class FakeNative:
    def __init__(self, rows):
        self.panes = {address(row): row for row in rows}
        self.calls = []
        self.fail_close = False
        self.queue = []
        self.source = None
        self.target = None
        self.fail_ship = False
        self.fail_queue = False

    def inventory(self):
        return copy.deepcopy(self.panes)

    def resting(self, session, window, require_agent=False):
        row = self.panes[session + "/" + window]
        if row["agent_state"] not in {"none", "done", "idle", "errored"} or self.queue:
            raise ValueError("not at rest or queued")

    def call(self, *args, **kwargs):
        self.calls.append(args)
        if args[0] == "capture-pane":
            return "saved pane output"
        if args[0] == "close-window":
            if self.fail_close:
                raise ValueError("forbidden")
            del self.panes[args[2] + "/" + args[3]]
            return {"success": True}
        if args[0] == "queue":
            if self.fail_queue:
                raise ValueError("uncertain transport")
            return {"success": True, "id": "q1"}
        if args[0] == "ship":
            if self.fail_ship:
                raise ValueError("merge_conflict")
            if args[1] == "commit":
                git(self.source, "add", "-A")
                git(self.source, "commit", "-m", "checked candidate")
            else:
                branch = git(self.source, "branch", "--show-current").strip()
                if "--squash" in args:
                    git(self.target, "merge", "--squash", branch)
                    git(self.target, "commit", "-m", "checked integration")
                else:
                    git(self.target, "merge", "--ff-only", branch)
            return {"success": True}
        raise AssertionError(args)


def git(cwd, *args):
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        env=runtime.environment(),
        timeout=15,
    )
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout


class RepoTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.repo = self.directory / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.name", "Test")
        git(self.repo, "config", "user.email", "test@example.invalid")
        git(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "file.txt").write_text("seed\n")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-m", "seed")

    def plan(self, code="print('check output')", timeout=3):
        return [
            {"name": "unit", "argv": [sys.executable, "-c", code], "timeout_s": timeout}
        ]

    def run_checks(self, plan=None, output="checks", cwd=None):
        return checks.run_plan(
            plan or self.plan(),
            cwd or self.repo,
            self.directory / output,
            platform.system(),
        )


class CheckTests(RepoTest):
    def test_pass_logs_identity_and_no_terminal_commands(self):
        result = self.run_checks()
        self.assertTrue(result["passed"])
        self.assertEqual(result["before"], result["after"])
        self.assertEqual(result["system"], platform.system())
        self.assertIn("check output", Path(result["checks"][0]["log"]).read_text())
        self.assertEqual(runtime.load(self.directory / "checks/result.json"), result)

    def test_failure_does_not_skip_later_checks(self):
        plan = self.plan("import sys; print('failure'); sys.exit(7)")
        plan += [
            {
                "name": "second",
                "argv": [sys.executable, "-c", "print('second')"],
                "timeout_s": 3,
            }
        ]
        result = self.run_checks(plan)
        self.assertFalse(result["passed"])
        self.assertEqual(result["checks"][0]["exit_code"], 7)
        self.assertEqual(result["checks"][1]["exit_code"], 0)

    def test_timeout_and_background_descendants_are_stopped(self):
        marker = self.directory / "child-finished"
        code = (
            "import subprocess, sys, time; "
            "subprocess.Popen([sys.executable, '-c', "
            + repr(
                f"import time; from pathlib import Path; time.sleep(0.6); Path({str(marker)!r}).touch()"
            )
            + "]); time.sleep(20)"
        )
        result = self.run_checks(self.plan(code, 0.15))
        self.assertFalse(result["passed"])
        self.assertEqual(result["checks"][0]["status"], "timeout")
        time.sleep(0.8)
        self.assertFalse(marker.exists())

    def test_launch_failure_is_recorded(self):
        result = self.run_checks(
            [{"name": "absent", "argv": ["/absent/dispatch-command"], "timeout_s": 2}]
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["checks"][0]["status"], "launch_error")

    def test_changed_checkout_is_not_passing_evidence(self):
        result = self.run_checks(
            self.plan(
                "from pathlib import Path; Path('file.txt').write_text('changed')"
            )
        )
        self.assertFalse(result["passed"])
        self.assertNotEqual(result["before"], result["after"])

    def test_untracked_content_changes_identity(self):
        path = self.repo / "untracked"
        path.write_text("one")
        before = runtime.identity(self.repo)
        path.write_text("two")
        self.assertNotEqual(before, runtime.identity(self.repo))

    def test_reject_wrong_platform_bad_plan_and_overwrite(self):
        with self.assertRaises(ValueError):
            checks.run_plan(
                self.plan(), self.repo, self.directory / "wrong", "NotThisOS"
            )
        self.assertFalse((self.directory / "wrong").exists())
        for plan in (
            [],
            [{}],
            self.plan(timeout=-1),
            self.plan(timeout=float("inf")),
            self.plan() * 2,
        ):
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                checks.validate(plan)
        self.run_checks()
        with self.assertRaises(FileExistsError):
            self.run_checks()

    def test_evidence_cannot_be_in_checkout(self):
        with self.assertRaises(ValueError):
            checks.run_plan(
                self.plan(), self.repo, self.repo / "evidence", platform.system()
            )

    def test_termination_records_interruption_and_stops_child(self):
        plan = self.directory / "plan.json"
        runtime.save(
            plan, self.plan("import time; print('READY', flush=True); time.sleep(20)")
        )
        output = self.directory / "interrupted"
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "scripts/checks.py"),
                "--plan",
                str(plan),
                "--cwd",
                str(self.repo),
                "--output",
                str(output),
                "--require-system",
                platform.system(),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                log = output / "001.log"
                if log.exists() and "READY" in log.read_text():
                    break
                time.sleep(0.02)
            else:
                self.fail("check did not become ready")
            process.terminate()
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 1, stderr)
            result = runtime.load(output / "result.json")
            self.assertEqual(result["checks"][0]["status"], "interrupted")
            self.assertFalse(result["passed"])
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_explicit_subdirectory_is_used(self):
        (self.repo / "subdir").mkdir()
        result = self.run_checks(
            self.plan("import os; print(os.path.basename(os.getcwd()))"),
            cwd=self.repo / "subdir",
        )
        self.assertIn("subdir", Path(result["checks"][0]["log"]).read_text())

    def test_cli_exit_codes(self):
        plan = self.directory / "plan.json"
        runtime.save(plan, self.plan("raise SystemExit(3)"))
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/checks.py"),
                "--plan",
                str(plan),
                "--cwd",
                str(self.repo),
                "--output",
                str(self.directory / "cli-checks"),
                "--require-system",
                platform.system(),
            ],
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertTrue(Path(result.stdout.strip()).is_file())


class WorkspaceTests(RepoTest):
    def setUp(self):
        super().setUp()
        self.run = self.directory / "run"
        self.native = FakeNative([pane(DISPATCH), pane(UNRELATED, "personal")])
        args = argparse.Namespace(
            run_dir=self.run,
            repo=self.repo,
            server="test",
            session="dispatch",
            dispatch=DISPATCH,
        )
        with patch.object(workspace, "Native", return_value=self.native):
            workspace.initialize(args)
        self.state = runtime.load(self.run / "run.json")

    def register(self, window=WORKER, role="aven", session="dispatch", system=None):
        row = pane(window, session)
        self.native.panes[address(row)] = row
        return workspace.register(
            self.state,
            self.native,
            argparse.Namespace(
                command="register",
                session=session,
                window=window,
                role=role,
                system=system,
            ),
        )

    def test_cleanup_keeps_dispatch_and_unrelated_windows(self):
        self.register()
        result = workspace.cleanup(self.state, self.native, self.run, True)
        self.assertTrue(result["ok"])
        self.assertEqual(
            set(self.native.panes), {"dispatch/" + DISPATCH, "personal/" + UNRELATED}
        )
        self.assertEqual(
            (self.run / (WORKER + ".log")).read_text(), "saved pane output"
        )
        # Resume is idempotent: never repeat a close for a pane now absent.
        calls = len(self.native.calls)
        workspace.cleanup(self.state, self.native, self.run, True)
        self.assertEqual(len(self.native.calls), calls)

    def test_close_only_removes_the_selected_owned_resource(self):
        self.register()
        self.register(window=UNKNOWN, role="auxiliary")
        result = workspace.cleanup(
            self.state, self.native, self.run, True, "dispatch/" + UNKNOWN
        )
        self.assertTrue(result["ok"])
        self.assertNotIn("dispatch/" + UNKNOWN, self.native.panes)
        self.assertIn("dispatch/" + WORKER, self.native.panes)
        with self.assertRaises(ValueError):
            workspace.cleanup(
                self.state, self.native, self.run, True, "dispatch/" + DISPATCH
            )

    def test_unknown_window_is_not_closed_and_fails_audit(self):
        self.native.panes["dispatch/" + UNKNOWN] = pane(UNKNOWN)
        result = workspace.cleanup(self.state, self.native, self.run, True)
        self.assertFalse(result["ok"])
        self.assertIn("dispatch/" + UNKNOWN, self.native.panes)
        self.assertEqual(self.native.calls, [])

    def test_existing_unrelated_and_dispatch_cannot_be_adopted(self):
        for session, window in (("personal", UNRELATED), ("dispatch", DISPATCH)):
            with self.assertRaises(ValueError):
                workspace.register(
                    self.state,
                    self.native,
                    argparse.Namespace(
                        command="register", session=session, window=window, role="aven"
                    ),
                )

    def test_unknown_unrelated_can_be_excluded_not_closed(self):
        self.native.panes["personal/" + UNKNOWN] = pane(UNKNOWN, "personal")
        workspace.register(
            self.state,
            self.native,
            argparse.Namespace(command="exclude", session="personal", window=UNKNOWN),
        )
        self.assertTrue(workspace.inspect(self.state, self.native)["ok"])
        self.assertTrue(
            workspace.cleanup(self.state, self.native, self.run, True)["ok"]
        )

    def test_active_queued_and_prompted_workers_block_cleanup(self):
        self.register()
        for state in ("working", "unknown", "needs_input"):
            self.native.panes["dispatch/" + WORKER]["agent_state"] = state
            self.assertFalse(
                workspace.cleanup(self.state, self.native, self.run, True)["ok"]
            )
        self.native.panes["dispatch/" + WORKER]["agent_state"] = "idle"
        self.native.queue = ["queued"]
        self.assertFalse(
            workspace.cleanup(self.state, self.native, self.run, True)["ok"]
        )
        self.assertIn("dispatch/" + WORKER, self.native.panes)
        self.assertEqual(self.native.calls, [])

    def test_failed_close_and_missing_dispatch_are_not_success(self):
        self.register()
        self.native.fail_close = True
        self.assertFalse(
            workspace.cleanup(self.state, self.native, self.run, True)["ok"]
        )
        del self.native.panes["dispatch/" + DISPATCH]
        count = len(self.native.calls)
        with self.assertRaises(ValueError):
            workspace.cleanup(self.state, self.native, self.run, True)
        self.assertEqual(len(self.native.calls), count)

    def test_evidence_ack_required(self):
        self.register()
        with self.assertRaises(ValueError):
            workspace.cleanup(self.state, self.native, self.run, False)
        self.assertFalse(self.native.calls)

    def test_failed_inventory_cannot_leave_a_passing_cached_report(self):
        runtime.save(self.run / "inventory.json", {"ok": True, "panes": {}})
        with (
            patch.object(workspace, "Native", return_value=self.native),
            patch.object(self.native, "inventory", side_effect=ValueError("host down")),
            patch("sys.stderr"),
        ):
            code = workspace.main(["--run-dir", str(self.run), "status"])
        self.assertEqual(code, 2)
        cached = runtime.load(self.run / "inventory.json")
        self.assertFalse(cached["ok"])
        self.assertEqual(cached["panes"], {})

    def test_registered_auxiliary_windows_pass_during_run_and_need_cleanup(self):
        self.register(role="auxiliary")
        self.native.panes["dispatch/" + WORKER]["focused"] = False
        self.assertTrue(workspace.inspect(self.state, self.native)["ok"])
        self.assertFalse(workspace.inspect(self.state, self.native, final=True)["ok"])
        self.assertTrue(
            workspace.cleanup(self.state, self.native, self.run, True)["ok"]
        )

    def test_linux_role_needs_host_evidence_and_full_uuid(self):
        with self.assertRaises(ValueError):
            self.register(role="linux-worker")
        self.register(role="linux-worker", system="Linux")
        with self.assertRaises(ValueError):
            workspace.key("dispatch", "10000000")

    def queue_args(self):
        self.register(role="linux-worker", system="Linux")
        self.native.panes["dispatch/" + WORKER]["agent_state"] = "working"
        prompt = self.directory / "followup.txt"
        prompt.write_text("Apply the reviewed correction.")
        return argparse.Namespace(
            session="dispatch", window=WORKER, id="task/repair-1", prompt_file=prompt
        )

    def test_followup_is_submitted_once_and_never_silently_changed(self):
        args = self.queue_args()
        first = workspace.queue_once(self.state, self.native, self.run, args)
        second = workspace.queue_once(self.state, self.native, self.run, args)
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "submitted")
        self.assertEqual(len(self.native.calls), 1)
        args.prompt_file.write_text("Different work.")
        with self.assertRaises(ValueError):
            workspace.queue_once(self.state, self.native, self.run, args)
        self.assertEqual(len(self.native.calls), 1)

    def test_uncertain_followup_is_not_retried(self):
        args = self.queue_args()
        self.native.fail_queue = True
        with self.assertRaises(ValueError):
            workspace.queue_once(self.state, self.native, self.run, args)
        saved = runtime.load(self.run / "run.json")
        self.assertEqual(saved["followups"][args.id]["status"], "pending")
        with self.assertRaises(ValueError):
            workspace.queue_once(saved, self.native, self.run, args)
        self.assertEqual(len(self.native.calls), 1)

    def test_followup_never_types_into_blocked_worker(self):
        args = self.queue_args()
        self.native.panes["dispatch/" + WORKER]["agent_state"] = "needs_input"
        with self.assertRaises(ValueError):
            workspace.queue_once(self.state, self.native, self.run, args)
        self.assertFalse(self.native.calls)

    def test_concurrent_scripts_fail_closed(self):
        with runtime.lock(self.run):
            with self.assertRaises(ValueError):
                with runtime.lock(self.run):
                    pass


class NativeContractTests(unittest.TestCase):
    def native(self, hosts=None, panes=None):
        native = runtime.Native("fixture")
        host_value = {
            "hosts": hosts if hosts is not None else [{"host": "local", "status": "up"}]
        }
        pane_value = {"panes": panes or []}
        native.call = lambda *args, **kw: host_value if args[0] == "ls" else pane_value
        return native

    def test_inventory_host_qualified_keys(self):
        native = self.native(
            [{"host": "build", "status": "up"}], [pane(WORKER, "build:task")]
        )
        self.assertIn("build:task/" + WORKER, native.inventory())

    def test_unavailable_host_and_unknown_schema_fail_closed(self):
        with self.assertRaises(ValueError):
            self.native([{"host": "build", "status": "down"}]).inventory()
        native = runtime.Native("")
        native.call = lambda *args: []
        with self.assertRaises(ValueError):
            native.inventory()

    def test_resting_rejects_unknown_state_and_queue(self):
        native = runtime.Native("")
        for state, entries in (
            ("working", []),
            ("needs_input", []),
            ("unknown", []),
            ("idle", [{"id": "q1"}]),
        ):
            native.call = lambda *args: (
                {"agents": [{"window_id": WORKER, "state": state}]}
                if args[0] == "list-agents"
                else {"entries": entries}
            )
            with (
                self.subTest(state=state, entries=entries),
                self.assertRaises(ValueError),
            ):
                native.resting("task", WORKER)

    def test_missing_worker_state_is_not_rest(self):
        native = runtime.Native("")
        native.call = lambda *args: {"agents": []}
        with self.assertRaises(ValueError):
            native.resting("task", WORKER, require_agent=True)

    def test_default_server_route_does_not_follow_changed_environment(self):
        with patch.object(runtime, "capture", return_value=b'{"success":true}') as call:
            runtime.Native("").call("ls", "--json")
        self.assertEqual(call.call_args.args[0], ["tuios", "ls", "--json"])
        self.assertEqual(call.call_args.kwargs["extra_env"], {"TUIOS_SERVER": ""})


class DeliveryTests(RepoTest):
    def setUp(self):
        super().setUp()
        self.source = self.directory / "source"
        git(self.repo, "worktree", "add", "-b", "task", str(self.source))
        (self.source / "file.txt").write_text("reviewed result\n")
        result = self.run_checks(cwd=self.source)
        self.assertTrue(result["passed"])
        self.integration = self.directory / "integration-plan.json"
        runtime.save(self.integration, self.plan())
        self.native = FakeNative([pane(WORKER, "task", "done", self.source)])
        self.native.source, self.native.target = self.source, self.repo
        self.state = {
            "server": "test",
            "owned": {"task/" + WORKER: {"role": "auxiliary"}},
        }
        self.args = argparse.Namespace(
            session="task",
            window=WORKER,
            cwd=self.source,
            target_repo=self.repo,
            into="main",
            checks=self.directory / "checks/result.json",
            integration_plan=self.integration,
            output=self.directory / "delivery",
            policy="squash",
            message="Reviewed change",
            reviewed=True,
        )

    def invoke(self):
        with patch.object(deliver, "Native", return_value=self.native):
            return deliver.deliver(self.args, self.state)

    def test_ship_and_integrated_checks_with_saved_steps(self):
        result = self.invoke()
        self.assertEqual(result["status"], "delivered")
        self.assertEqual((self.repo / "file.txt").read_text(), "reviewed result\n")
        self.assertEqual(
            [row["status"] for row in result["steps"]], ["returned", "returned"]
        )
        self.assertEqual(
            runtime.load(self.args.output / "result.json")["status"], "delivered"
        )
        with self.assertRaises(ValueError):  # evidence no longer names the candidate
            self.invoke()

    def test_stale_check_evidence_blocks_all_native_writes(self):
        (self.source / "file.txt").write_text("unchecked result\n")
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertFalse(self.native.calls)

    def test_dirty_target_review_and_queue_gate_delivery(self):
        (self.repo / "other.txt").write_text("personal")
        with self.assertRaises(ValueError):
            self.invoke()
        (self.repo / "other.txt").unlink()
        self.args.reviewed = False
        with self.assertRaises(ValueError):
            self.invoke()
        self.args.reviewed = True
        self.native.queue = ["pending"]
        with self.assertRaises(ValueError):
            self.invoke()
        self.assertFalse(self.native.calls)

    def test_native_failure_is_journaled_and_not_retried(self):
        self.native.fail_ship = True
        result = self.invoke()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["steps"][0]["status"], "pending")
        self.assertEqual(len(self.native.calls), 1)
        with self.assertRaises(FileExistsError):
            self.invoke()
        self.assertEqual(len(self.native.calls), 1)

    def test_integrated_failure_is_not_reported_as_delivery_success(self):
        runtime.save(self.integration, self.plan("raise SystemExit(9)"))
        result = self.invoke()
        self.assertEqual(result["status"], "integration_failed")
        self.assertEqual((self.repo / "file.txt").read_text(), "reviewed result\n")

    def test_fast_forward_policy(self):
        self.args.policy = "ff-only"
        result = self.invoke()
        self.assertEqual(result["status"], "delivered")
        self.assertEqual(
            git(self.repo, "rev-parse", "HEAD"), git(self.source, "rev-parse", "HEAD")
        )


class DashboardAutomationTests(unittest.TestCase):
    def test_observe_replaces_stale_state_and_report_opens_no_window(self):
        snapshot = runtime.load(ROOT / "assets/dashboard-example.json")
        row = snapshot["tasks"][0]
        row["session"], row["pane"] = "build:task", WORKER
        value = {
            "ok": True,
            "observed_at": time.time(),
            "panes": {"build:task/" + WORKER: {"agent_state": "working"}},
        }
        current = dashboard.observe(snapshot, value)
        self.assertEqual(current["revision"], snapshot["revision"] + 1)
        self.assertEqual(current["tasks"][0]["native"]["state"], "working")
        missing = dashboard.observe(
            current, {"ok": True, "observed_at": time.time(), "panes": {}}
        )
        self.assertEqual(missing["tasks"][0]["native"]["state"], "unknown")
        for stale in (
            {"ok": False, "observed_at": time.time(), "panes": {}},
            {"ok": True, "observed_at": time.time() - 61, "panes": {}},
        ):
            with self.assertRaises(ValueError):
                dashboard.observe(current, stale)
        self.assertIn("Dispatch:", dashboard.report(missing))
        self.assertTrue(
            all(len(line) <= 80 for line in dashboard.report(missing).splitlines())
        )


if __name__ == "__main__":
    unittest.main()
