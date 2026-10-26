"""Deterministic input, summary, retention, routing, and growth contracts."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import test_documented_workflow as workflow
import test_launch as launch
import test_safety as safety

sys.path.insert(0, str(launch.SCRIPTS))
import dispatch
from dispatch_lib import output, prompts, recovery, stop


class ContractTests(unittest.TestCase):
    def args(self, **values):
        return SimpleNamespace(
            command="launch", task="APP-TEST", verbose=False, **values
        )

    def record(self):
        return {
            "ok": True,
            "task_ref": "APP-TEST",
            "handle": "dispatch-app-test",
            "record_path": "/repo/.git/dispatch-workers/APP-TEST/worker.json",
            "launch_base": "a" * 40,
            "next_action": "review/monitor",
            "events": [
                {
                    "action": "launch",
                    "activation": {"status": "active"},
                    "containers": [
                        {"mounts": [{"source": "/repo", "destination": "/work"}]}
                    ],
                    "launch_output": "large log\n" * 10000,
                }
            ],
        }

    def test_history_and_mount_growth_does_not_change_summary(self):
        record = self.record()
        expected = output.summary(record, self.args())
        for count in (1, 10, 100, 1000):
            large = dict(record, events=record["events"] * count)
            self.assertEqual(output.summary(large, self.args()), expected)
            self.assertLess(len(json.dumps(expected).encode()), 1500)
        for field in ("events", "containers", "mounts", "launch_output"):
            self.assertNotIn(field, expected)
        self.assertEqual(expected["status"], "active")

    def test_large_pending_cleanup_errors_and_housekeeping_are_bounded(self):
        entries = [
            {
                "resource": "worktree",
                "identity": "x" * 10000,
                "owner": "dispatcher",
                "next_action": "repair " * 10000,
                "status": "pending",
            }
        ] * 1000
        data = dict(
            self.record(),
            delivered=True,
            task_complete=True,
            finish_complete=False,
            pending_cleanup=entries,
            housekeeping=entries,
            errors=["failure " * 10000] * 1000,
        )
        result = output.summary(data, self.args(), "/durable/evidence.json")
        self.assertTrue(result["delivered"])
        self.assertTrue(result["task_complete"])
        self.assertFalse(result["finish_complete"])
        self.assertEqual(result["pending_cleanup"]["count"], 1000)
        self.assertEqual(result["housekeeping"]["more"], 997)
        self.assertEqual(result["owner"], "dispatcher")
        self.assertLess(len(json.dumps(result).encode()), output.SUMMARY_BUDGET)

    def test_inspection_uses_current_outcome_not_saved_launch_error(self):
        data = dict(
            self.record(),
            error="old activation failure",
            inspection={"ok": True, "workmux_status": {"agents": [{"status": "done"}]}},
        )
        result = output.summary(data, self.args())
        self.assertTrue(result["ok"])
        self.assertNotIn("error", result)
        self.assertEqual(result["worker_status"], "done")
        data.update(
            ok=False, inspection={"ok": False, "error": "mount identity changed"}
        )
        result = output.summary(data, self.args())
        self.assertFalse(result["ok"])
        self.assertIn("mount identity", result["error"])

    def test_finish_inspection_exposes_writer_and_saved_failure(self):
        data = {
            "ok": True,
            "inspection": {"worktree_present": True, "branch_present": True},
            "writer": {"ok": False, "error": "Container identity changed"},
            "saved_finish": {
                "delivered": False,
                "task_complete": False,
                "error": "Writer exit was not confirmed",
            },
        }
        result = output.summary(data, self.args())
        self.assertTrue(result["ok"])  # The read-only query itself completed.
        self.assertEqual(result["status"], "observed")
        self.assertFalse(result["writer_ok"])
        self.assertFalse(result["writer_stopped"])
        self.assertFalse(result["task_complete"])
        self.assertIn("identity changed", result["writer_error"])
        self.assertIn("not confirmed", result["saved_finish_error"])
        self.assertEqual(result["owner"], "dispatcher")

    def test_embedded_error_receipts_do_not_leak_mounts_into_summary(self):
        receipt = {
            "error": "Exact worker mount changed",
            "receipt": {"container": {"mounts": ["private-mount"] * 10000}},
        }
        data = {"ok": False, "error": "Cannot stop worker: " + json.dumps(receipt)}
        result = output.summary(data, self.args())
        self.assertIn("Exact worker mount changed", result["error"])
        self.assertNotIn("private-mount", json.dumps(result))
        self.assertNotIn("receipt", json.dumps(result))

    def test_report_size_is_independent_of_note_length(self):
        for count in (1000, 100000):
            result = output.summary(
                {
                    "ok": True,
                    "note": {"id": "note-id", "body": "RESULT: " + "evidence " * count},
                },
                self.args(),
                "/durable/report.json",
            )
            self.assertLess(len(json.dumps(result).encode()), 1200)
            self.assertEqual(result["note"]["id"], "note-id")
            self.assertEqual(result["evidence_path"], "/durable/report.json")

    def test_references_are_not_truncated(self):
        path = "/" + "deep/" * 200 + "evidence.json"
        result = output.summary(
            dict(self.record(), record_path=path), self.args(), path
        )
        self.assertEqual(result["record_path"], path)
        self.assertEqual(result["evidence_path"], path)

    def test_complete_evidence_and_exit_code_are_preserved(self):
        data = dict(self.record(), ok=False, error="failure " * 10000)
        with tempfile.TemporaryDirectory() as directory:
            args = self.args()
            with patch.object(output, "paths", return_value={"common_dir": directory}):
                with contextlib.redirect_stdout(io.StringIO()) as stream:
                    code = output.invoke(lambda _: data, args)
                compact = json.loads(stream.getvalue())
                evidence = json.loads(Path(compact["evidence_path"]).read_text())
                self.assertEqual(evidence, data)
                self.assertEqual(code, 1)
                self.assertLess(len(stream.getvalue().encode()), 2000)
                args.verbose = True
                with contextlib.redirect_stdout(io.StringIO()) as stream:
                    self.assertEqual(output.invoke(lambda _: data, args), 1)
                full = json.loads(stream.getvalue())
                self.assertEqual(full["error"], data["error"])

    def test_read_only_output_never_writes_evidence(self):
        args = SimpleNamespace(
            command="inspect", task="APP-TEST", resume=False, verbose=False
        )
        with patch.object(output, "retain", side_effect=AssertionError("write")):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(output.invoke(lambda _: self.record(), args), 0)

    def test_existing_record_is_referenced_not_recopied(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "worker.json"
            path.write_text("{}")
            data = dict(self.record(), schema_version=1, record_path=str(path))
            with patch.object(
                output, "paths", side_effect=AssertionError("duplicate receipt")
            ):
                self.assertEqual(output.retain(data, self.args()), path)

    def test_failed_evidence_write_cannot_report_success(self):
        with patch.object(output, "retain", side_effect=OSError("disk full")):
            with contextlib.redirect_stdout(io.StringIO()) as stream:
                code = output.invoke(lambda _: {"ok": True}, self.args())
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(stream.getvalue())["ok"])
        self.assertIn("disk full", stream.getvalue())

    def test_prompt_preserves_requirements_decisions_and_scoped_context(self):
        description = "Acceptance: preserve safety.\n" * 10000
        context = {
            "task": {
                "id": "private-id",
                "display_ref": "APP-TEST",
                "title": "Required task",
                "description": description,
            },
            "notes": [
                {"id": str(i), "body": "DECISION: keep authorization"}
                for i in range(1000)
            ],
            "dependencies": {"requires": ["APP-OTHER"]},
            "attachments": ["spec.md"],
        }
        text = prompts.scoped_context(context)
        self.assertIn(description, text)
        self.assertEqual(text.count("DECISION: keep authorization"), 1)
        self.assertNotIn("private-id", text)
        self.assertIn("APP-OTHER", text)
        self.assertIn("spec.md", text)
        self.assertLess(len(text.encode()), len(description.encode()) + 350)
        with patch.object(prompts, "run", side_effect=AssertionError("second fetch")):
            prompt = prompts.render(
                "APP-TEST",
                base="main",
                launch_base="a" * 40,
                branch="dispatch/app-test",
                acceptance_checks=[["echo", "a b"]],
                context=text,
            )
        self.assertEqual(prompt.count("# Worker contract"), 1)
        self.assertIn("echo 'a b'", prompt)

    def test_stop_receipt_does_not_embed_events_or_previous_receipts(self):
        record = dict(
            self.record(),
            runtime="local",
            common_dir="/git",
            worktree="/worker",
            worker_worktree="/guest",
            finish={"exit_evidence": {"receipt": self.record()}},
        )
        evidence = stop.stop(record)
        self.assertNotIn("events", evidence["receipt"])
        self.assertNotIn("finish", evidence["receipt"])
        self.assertEqual(evidence["receipt"]["task_ref"], "APP-TEST")
        self.assertLess(len(json.dumps(evidence).encode()), 1000)

    def test_consolidated_baseline_fixture_and_growth_budget(self):
        data = json.loads(
            (Path(__file__).parent / "fixtures/io-baseline.json").read_text()
        )
        expected = None
        for count, full_bytes in ((1, 6962), (10, 41036), (100, 381776)):
            sample = dict(data, events=data["events"] * count)
            self.assertEqual(len(json.dumps(sample, indent=2).encode()), full_bytes)
            result = output.summary(sample, self.args(), data["record_path"])
            self.assertEqual(len(json.dumps(result, indent=2).encode()), 550)
            if expected is not None:
                self.assertEqual(result, expected)
            expected = result

    def test_phase_arguments_and_resume_are_separate(self):
        cli = dispatch.parser()
        for command in (
            "startup",
            "launch",
            "inspect",
            "resume",
            "finish",
            "close-run",
        ):
            args = cli.parse_args([command, "APP-TEST"])
            self.assertTrue(callable(args.handler))
        args = cli.parse_args(["resume", "APP-TEST"])
        self.assertTrue(args.resume)
        self.assertEqual(args.command, "resume")
        for argv in (
            ["inspect", "APP-TEST", "--resume"],
            ["inspect", "APP-TEST", "--base", "main"],
            ["resume", "APP-TEST", "--check", '["true"]'],
        ):
            with (
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                cli.parse_args(argv)

    def test_all_phase_help_is_available_without_external_commands(self):
        commands = [
            (name,)
            for name in (
                "startup",
                "launch",
                "inspect",
                "resume",
                "report",
                "integrate",
                "finish",
                "close-run",
                "doctor",
            )
        ]
        commands += [
            ("recover", name)
            for name in (
                "snapshot",
                "preflight",
                "verify",
                "stop",
                "archive",
                "cleanup",
            )
        ]
        for command in commands:
            with self.subTest(command=command):
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    self.assertRaises(SystemExit) as raised,
                ):
                    dispatch.parser().parse_args([*command, "--help"])
                self.assertEqual(raised.exception.code, 0)


class CompactLifecycleTests(unittest.TestCase):
    setUp = launch.LaunchTests.setUp
    git = launch.LaunchTests.git
    calls = launch.LaunchTests.calls
    start = workflow.DocumentedWorkflowTests.start
    cli = launch.LaunchTests.cli
    prepare_run = launch.LaunchTests.prepare_run
    completed_record = launch.LaunchTests.completed_record
    command = workflow.DocumentedWorkflowTests.command

    def compact(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(launch.SCRIPTS / "dispatch.py"), *args],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stdout + result.stderr
        )
        self.assertLess(len(result.stdout.encode()), output.SUMMARY_BUDGET)
        data = json.loads(result.stdout)
        self.assertIs(data["ok"], ok)
        return data

    def test_compact_lifecycle_and_durable_evidence_after_cleanup(self):
        self.start()
        before = self.record.read_bytes()
        files = sorted(str(p) for p in (self.repo / ".git").rglob("*"))
        inspected = self.compact("inspect", "APP-TEST", "--wait", "1")
        self.assertEqual(self.record.read_bytes(), before)
        self.assertEqual(sorted(str(p) for p in (self.repo / ".git").rglob("*")), files)
        self.assertNotIn("events", inspected)
        report = self.compact("report", "--task", "APP-TEST")
        self.assertEqual(report["note"]["id"], "result-1")
        integrated = self.compact("integrate", *self.review)
        self.assertEqual(len(integrated["verified_base_sha"]), 40)
        completed = self.compact("finish", "APP-TEST")
        self.assertTrue(completed["delivered"])
        self.assertTrue(completed["task_complete"])
        self.assertEqual(completed["pending_cleanup"]["count"], 0)
        self.assertFalse(self.worker.exists())
        for result in (report, integrated, completed):
            evidence = json.loads(Path(result["evidence_path"]).read_text())
            self.assertTrue(evidence["ok"])
        self.assertTrue(Path(report["source_path"]).is_file())
        observed = self.compact("finish", "APP-TEST", "--inspect")
        self.assertTrue(observed["task_complete"])
        # This fixture deliberately has an unclosed host UI and unsafe parent.
        self.assertGreater(completed["housekeeping"]["count"], 0)
        self.assertFalse(completed["finish_complete"])

    def test_compact_closure_after_all_saved_work_and_housekeeping_complete(self):
        self.completed_record()
        self.env["AVEN_INITIAL_STATUS"] = "done"
        self.env["WRITE_SUMMARY"] = "1"
        closed = self.compact("close-run", "APP-TEST", "--authorize-close")
        self.assertTrue(closed["aven_closed"])
        self.assertNotIn("worker_reconciliation", closed)
        self.assertTrue(Path(closed["record_path"]).is_file())

    def test_missing_lock_inspection_does_not_create_files_or_worker(self):
        self.start()
        lock = self.repo / ".git/dispatch.lock"
        lock.unlink()
        before = self.record.read_bytes()
        files = sorted(str(p) for p in (self.repo / ".git").rglob("*"))
        result = self.compact("inspect", "APP-TEST", ok=False)
        self.assertIn("dispatch.lock", result["error"])
        self.assertFalse(lock.exists())
        self.assertEqual(self.record.read_bytes(), before)
        self.assertEqual(sorted(str(p) for p in (self.repo / ".git").rglob("*")), files)
        self.assertEqual(sum(c[:2] == ["workmux", "add"] for c in self.calls()), 1)

    def test_compact_failure_and_pending_cleanup_remain_actionable(self):
        self.start(partial=True)
        self.compact("integrate", *self.review)
        artifact = self.worker / "unknown"
        artifact.write_text("preserve")
        completed = self.compact("finish", "APP-TEST")
        self.assertTrue(completed["delivered"])
        self.assertTrue(completed["task_complete"])
        self.assertFalse(completed["finish_complete"])
        self.assertGreater(completed["pending_cleanup"]["count"], 0)
        self.assertEqual(completed["owner"], "dispatcher")
        self.assertTrue(artifact.exists())
        failure = self.compact("close-run", "APP-TEST", "--authorize-close", ok=False)
        self.assertIn("pending cleanup", failure["error"])
        self.assertTrue(Path(failure["evidence_path"]).is_file())
        self.assertEqual(sum(c[:2] == ["workmux", "add"] for c in self.calls()), 1)


class LogEvidenceTests(unittest.TestCase):
    setUp = safety.SafetyTests.setUp
    git = safety.SafetyTests.git
    json_file = safety.SafetyTests.json_file
    cli = safety.SafetyTests.cli
    verify = safety.SafetyTests.verify

    def test_large_check_logs_are_durable_and_verbose_expands_them(self):
        size = 1200000
        result = self.verify(
            [
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stdout.write('x' * " + str(size) + ")",
                ]
            ]
        )
        self.assertEqual(len(result["checks"][0]["stdout"]), size)
        saved = json.loads(Path(result["evidence_path"]).read_text())
        check = saved["checks"][0]
        self.assertEqual(len(check["stdout"]), 4096)
        self.assertEqual(check["stdout_bytes"], size)
        self.assertTrue(check["stdout_truncated"])
        self.assertEqual(Path(check["stdout_path"]).read_bytes(), b"x" * size)
        self.assertFalse(Path(result["worktree"]).exists())
        self.assertLess(len(json.dumps(saved).encode()), 12000)

    def test_recovery_limit_fails_closed_without_losing_complete_log(self):
        result = recovery.command(
            [sys.executable, "-c", "print('x' * 100000)"], self.repo
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["truncated"])
        self.assertEqual(len(result["stdout"]), recovery.LIMIT)
        self.assertEqual(Path(result["stdout_path"]).stat().st_size, 100001)
        verbose = output.full_evidence(result)
        self.assertEqual(len(verbose["stdout"]), 100001)


if __name__ == "__main__":
    unittest.main()
