"""Documented public CLI sequence with real Git and controlled external tools."""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import test_launch as launch

EXTRA = r"""
phase = os.environ.get("PHASE", "launch")
if name == "aven" and phase != "launch":
    if args[0] == "edit":
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("task_ref")
        parser.add_argument("--status", choices=["done"], required=True)

        parser.parse_args(args[1:])
        (root / "aven-status").write_text("done")
    status = (root / "aven-status").read_text() if (root / "aven-status").exists() else "active"
    sha = git("rev-parse", "refs/heads/dispatch/app-test") if worker.exists() else ""
    print(json.dumps({"task": {"id": "task-id", "ref": args[1], "display_ref": args[1], "status": status}, "notes": [
        {"id": "result-1", "body": "RESULT: implemented " + sha,
         "created_at": "2026-10-20T00:00:00Z"}]}))
    sys.exit(0)
if name == "workmux" and args[0] == "merge":
    failure = os.environ.get("MERGE_FAILURE", "")
    if failure != "before":
        git("merge", "--ff-only", "dispatch/app-test")
    if failure:
        sys.stderr.write("controlled merge failure " + failure)
        sys.exit(9)
    sys.exit(0)
if name in ("docker", "container", "podman") and os.environ.get("UNCERTAIN_EXIT"):
    sys.stderr.write("container disappeared without confirmed stop")
    sys.exit(1)
if name in ("docker", "container", "podman") and args[0] == "stop":
    (root / "stopped").write_text("yes")
    sys.exit(0)
"""


class DocumentedWorkflowTests(unittest.TestCase):
    setUp = launch.LaunchTests.setUp
    git = launch.LaunchTests.git
    calls = launch.LaunchTests.calls

    def command(self, script, *args, ok=True):
        result = subprocess.run(
            [sys.executable, str(launch.SCRIPTS / script), *args, "--verbose"],
            cwd=self.repo,
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(
            result.returncode, 0 if ok else 1, result.stdout + result.stderr
        )
        return json.loads(result.stdout)

    def start(self, partial=False, task="APP-TEST", startup=True, check=None):
        fake = launch.FAKE.replace(
            'if name == "aven":', EXTRA + '\nif name == "aven":', 1
        )
        # Each sequential worker has its own path, branch, and task reference.
        fake = fake.replace(
            'worker = root / "worker"',
            'worker = Path(os.environ.get("TEST_WORKER", str(root / "worker")))',
        )
        if task != "APP-TEST":
            fake = fake.replace("APP-TEST", task).replace("app-test", task.lower())
        fake = fake.replace(
            '"Status": "running"',
            '"Status": "exited" if (root / "stopped").exists() else "running"',
        )
        for name in ("aven", "workmux", "docker", "container", "podman"):
            (self.root / "bin" / name).write_text(
                fake.replace("#!PYTHON", "#!" + sys.executable)
            )
        if startup:
            self.command("dispatch.py", "startup", "APP-TEST")
        self.env["MODE"] = "partial" if partial else ""
        self.command(
            "dispatch.py",
            "launch",
            task,
            "--run-id",
            "APP-TEST",
            "--base",
            "main",
            "--check",
            check or '["git", "diff", "--check"]',
            # Select Docker explicitly to exercise the same adapter on all hosts.
            "--runtime",
            "docker",
            ok=not partial,
        )
        if partial:
            self.env["MODE"] = ""
            self.command("dispatch.py", "resume", "APP-TEST")
        self.worker = Path(self.env.get("TEST_WORKER", str(self.root / "worker")))
        # Match repositories that ignore Workmux artifacts: receipt-listed,
        # unchanged prompts are still eligible for archival during finish.
        (self.repo / ".git/info/exclude").write_text(".workmux/\n")
        self.git("config", "user.name", "Workflow Test")
        self.git("config", "user.email", "workflow@example.invalid")
        (self.worker / "src").mkdir(exist_ok=True)
        (self.worker / "src/change").write_text(
            "delivered\n" if task == "APP-TEST" else "delivered\nsecond\n"
        )
        self.git("-C", str(self.worker), "add", "src/change")
        self.git("-C", str(self.worker), "commit", "-qm", "Implement task")
        self.env["PHASE"] = "reported"
        report = self.command("dispatch.py", "report", "--task", task)
        self.review = [
            task,
            "--reviewed-commit",
            report["worker_commit"],
            "--result-id",
            report["note"]["id"],
        ]

    def finish(self):
        result = self.command("dispatch.py", "finish", "APP-TEST")
        self.assertTrue(result["task_complete"])
        return result

    def test_successful_no_retry_managed_inventory(self):
        self.start()
        integrated = self.command("dispatch.py", "integrate", *self.review)
        completed = self.finish()
        self.assertEqual(completed["pending_cleanup"], [])
        self.assertFalse(self.worker.exists())
        directory = self.record.parent
        record = json.loads(self.record.read_text())
        self.assertEqual(record["agent_type"], "pi")
        edits = [call for call in self.calls() if call[:2] == ["aven", "edit"]]
        self.assertEqual(edits, [["aven", "edit", "APP-TEST", "--status", "done"]])
        prompt_copy = directory / ("prompt-" + record["prompts"][0]["sha256"] + ".md")
        integration = Path(integrated["evidence_directory"])
        expected = {
            self.record,
            directory / "assignment.md",
            directory / "task-context.json",
            directory / "config.yaml",
            prompt_copy,
            integration / "checks.json",
            integration / "worker-checks.json",
            integration / "base-verification.json",
            directory / "archive/PROMPT-test.md",
            directory / "completion.md",
        }
        actual = {path for path in directory.rglob("*") if path.is_file()}
        self.assertEqual(len(expected), 10)
        self.assertEqual(actual, expected)
        self.assertEqual(sum(c[:2] == ["workmux", "add"] for c in self.calls()), 1)
        self.assertEqual(sum(c[:2] == ["workmux", "merge"] for c in self.calls()), 1)

    def test_two_accepted_tasks_reconcile_and_close_after_base_advances(self):
        # JSON encode checks so shell quoting is not part of this test.
        one_line = json.dumps(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; assert Path('src/change').read_text() == 'delivered\\n'",
            ]
        )
        self.env["TEST_WORKER"] = str(self.root / "worker-a" / "tree")
        self.start(check=one_line)
        self.command("dispatch.py", "integrate", *self.review)
        path_a = self.record

        def finish_without_worker_ui(path, task):
            saved = json.loads(path.read_text())
            # This fixture has only the dispatcher UI. Worker UI cleanup is
            # covered by the separate real-socket finish tests.
            saved["ui"]["agents"] = []
            path.write_text(json.dumps(saved))
            result = self.command("dispatch.py", "finish", task)
            self.assertTrue(result["finish_complete"])
            return result

        completed_a = finish_without_worker_ui(path_a, "APP-TEST")
        before = path_a.read_bytes()
        self.env["PHASE"] = "launch"
        (self.root / "aven-status").write_text("active")
        self.env["TEST_WORKER"] = str(self.root / "worker-b" / "tree")
        (self.root / "stopped").unlink()
        # start() commits a new change. B replaces A's one-line result.
        # Reuse launch with B's own independent two-line acceptance check.
        two_lines = json.dumps(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; assert Path('src/change').read_text() == 'delivered\\nsecond\\n'",
            ]
        )
        self.start(task="APP-NEXT", startup=False, check=two_lines)
        self.command("dispatch.py", "integrate", *self.review)
        path_b = self.repo / ".git/dispatch-workers/APP-NEXT/worker.json"
        finish_without_worker_ui(path_b, "APP-NEXT")
        self.assertEqual(path_a.read_bytes(), before)
        self.env["TEST_WORKER"] = str(self.root / "worker-a" / "tree")
        inspected = self.command("dispatch.py", "finish", "APP-TEST", "--inspect")
        self.assertEqual(
            inspected["saved_finish"],
            {
                k: v
                for k, v in completed_a.items()
                if k
                not in (
                    "task_ref",
                    "handle",
                    "record_path",
                    "verified_base_sha",
                    "evidence_path",
                )
            },
        )
        self.assertEqual(path_a.read_bytes(), before)
        self.assertTrue(
            self.command("dispatch.py", "finish", "APP-TEST")["finish_complete"]
        )
        self.assertEqual(
            subprocess.run(
                json.loads(one_line), cwd=self.repo, capture_output=True, check=False
            ).returncode,
            1,
        )

        # Restore the startup fixture's multi-task Aven context and fresh SUMMARY.
        # It models Aven, not task-specific acceptance or finish behavior.
        (self.root / "bin/aven").write_text(
            launch.FAKE.replace("#!PYTHON", "#!" + sys.executable).replace(
                '"display_ref": os.environ.get("DISPLAY_REF", "APP-TEST")',
                '"display_ref": args[1]',
            )
        )
        self.env["WRITE_SUMMARY"] = "1"
        closed = self.command(
            "dispatch.py", "close-run", "APP-TEST", "--authorize-close"
        )
        self.assertTrue(closed["aven_closed"])
        self.assertEqual(
            {worker["task_ref"] for worker in closed["worker_reconciliation"]},
            {"APP-TEST", "APP-NEXT"},
        )

    def test_launch_review_integrate_finish_cleanup_retry(self):
        self.start(partial=True)
        self.assertEqual(sum(c[:2] == ["workmux", "add"] for c in self.calls()), 1)
        self.command("dispatch.py", "integrate", *self.review)
        # Unknown artifacts are preserved, but their cleanup remains visible after done.
        unknown = self.worker / "unknown-artifact"
        unknown.write_text("retain")
        first = self.finish()
        self.assertTrue(first["pending_cleanup"])
        self.assertTrue(unknown.exists())
        inspected = self.command("dispatch.py", "finish", "APP-TEST", "--inspect")
        self.assertTrue(inspected["saved_finish"]["pending_cleanup"])
        unknown.unlink()  # Explicit test-owner actions, not automatic cleanup.
        retried = self.command("dispatch.py", "finish", "APP-TEST")
        self.assertTrue(retried["task_complete"])
        self.assertEqual(retried["pending_cleanup"], [])
        self.assertFalse(self.worker.exists())

    def test_interrupted_integration_reconciles_without_second_merge(self):
        self.start()
        self.env["MERGE_FAILURE"] = "after"
        self.command("dispatch.py", "integrate", *self.review, ok=False)
        self.env["MERGE_FAILURE"] = ""
        self.command("dispatch.py", "integrate", *self.review, "--reconcile")
        self.assertEqual(sum(c[:2] == ["workmux", "merge"] for c in self.calls()), 1)
        self.finish()

    def test_uncertain_exit_blocks_completion_after_integration(self):
        self.start()
        self.command("dispatch.py", "integrate", *self.review)
        self.env["UNCERTAIN_EXIT"] = "1"
        result = self.command("dispatch.py", "finish", "APP-TEST", ok=False)
        self.assertFalse(result["task_complete"])
        self.assertFalse(result["delivered"])
        self.assertTrue(self.worker.exists())
        self.assertFalse(any(c[:2] == ["aven", "edit"] for c in self.calls()))

    def test_merge_failure_preserves_unintegrated_worker(self):
        self.start()
        self.env["MERGE_FAILURE"] = "before"
        self.command("dispatch.py", "integrate", *self.review, ok=False)
        self.command("dispatch.py", "integrate", *self.review, "--reconcile", ok=False)
        self.assertTrue(self.worker.exists())
        self.assertEqual(self.git("rev-parse", "main"), self.base)
        self.assertEqual(sum(c[:2] == ["workmux", "merge"] for c in self.calls()), 1)


class DocumentationTests(unittest.TestCase):
    def test_local_markdown_links_and_anchors(self):
        root = launch.SCRIPTS.parent
        for source in root.glob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", source.read_text()):
                if "://" in target:
                    continue
                filename, _, anchor = target.partition("#")
                path = source.parent / filename if filename else source
                self.assertTrue(path.exists(), f"{source}: {target}")
                if anchor:
                    headings = re.findall(r"^#+ (.+)$", path.read_text(), re.MULTILINE)
                    anchors = [
                        re.sub(r"[^\w -]", "", h.lower()).replace(" ", "-")
                        for h in headings
                    ]
                    self.assertIn(anchor, anchors, f"{source}: {target}")

    def test_documented_command_help(self):
        for script, extra in (
            ("dispatch.py", []),
            ("dispatch.py", ["report"]),
            ("dispatch.py", ["doctor"]),
            ("dispatch.py", ["integrate"]),
            ("dispatch.py", ["finish"]),
            ("dispatch.py", ["recover", "verify"]),
        ):
            result = subprocess.run(
                [sys.executable, str(launch.SCRIPTS / script), *extra, "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("usage:", result.stdout)
