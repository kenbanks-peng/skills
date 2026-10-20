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
        parser.add_argument("--db")
        parser.add_argument("--workspace")
        parser.parse_args(args[1:])
        (root / "aven-status").write_text("done")
    status = (root / "aven-status").read_text() if (root / "aven-status").exists() else "active"
    sha = git("rev-parse", "refs/heads/dispatch/app-test") if worker.exists() else ""
    print(json.dumps({"task": {"ref": "APP-TEST", "display_ref": "APP-TEST", "status": status}, "notes": [
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
            [sys.executable, str(launch.SCRIPTS / script), *args],
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

    def start(self, partial=False):
        fake = launch.FAKE.replace(
            'if name == "aven":', EXTRA + '\nif name == "aven":', 1
        )
        fake = fake.replace(
            '"Status": "running"',
            '"Status": "exited" if (root / "stopped").exists() else "running"',
        )
        for name in ("aven", "workmux", "docker", "container", "podman"):
            (self.root / "bin" / name).write_text(
                fake.replace("#!PYTHON", "#!" + sys.executable)
            )
        self.env["MODE"] = "partial" if partial else ""
        self.command(
            "dispatch.py",
            "launch",
            "APP-TEST",
            "--base",
            "main",
            "--check",
            '["git", "diff", "--check"]',
            # Select Docker explicitly to exercise the same adapter on all hosts.
            "--runtime",
            "docker",
            ok=not partial,
        )
        if partial:
            self.env["MODE"] = ""
            self.command("dispatch.py", "inspect", "APP-TEST", "--resume")
        self.worker = self.root / "worker"
        # Match repositories that ignore Workmux artifacts: receipt-listed,
        # unchanged prompts are still eligible for archival during finish.
        (self.repo / ".git/info/exclude").write_text(".workmux/\n")
        self.git("config", "user.name", "Workflow Test")
        self.git("config", "user.email", "workflow@example.invalid")
        (self.worker / "src").mkdir()
        (self.worker / "src/change").write_text("delivered\n")
        self.git("-C", str(self.worker), "add", "src/change")
        self.git("-C", str(self.worker), "commit", "-qm", "Implement task")
        self.env["PHASE"] = "reported"
        report = self.command("dispatch_cli.py", "report", "--task", "APP-TEST")
        self.review = [
            "APP-TEST",
            "--reviewed-commit",
            report["worker_commit"],
            "--result-id",
            report["note"]["id"],
        ]

    def finish(self):
        plan = self.command("finish_worker.py", "APP-TEST")
        self.assertTrue(plan["dry_run"])
        result = self.command("finish_worker.py", "APP-TEST", "--authorize-finish")
        self.assertTrue(result["task_complete"])
        return result

    def test_successful_no_retry_managed_inventory(self):
        self.start()
        integrated = self.command("integrate.py", *self.review)
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
            directory / "config.yaml",
            prompt_copy,
            integration / "checks.json",
            integration / "worker-checks.json",
            integration / "base-verification.json",
            directory / "archive/PROMPT-test.md",
            directory / "completion.md",
        }
        actual = {path for path in directory.rglob("*") if path.is_file()}
        self.assertEqual(len(expected), 9)
        self.assertEqual(actual, expected)
        self.assertEqual(sum(c[:2] == ["workmux", "add"] for c in self.calls()), 1)
        self.assertEqual(sum(c[:2] == ["workmux", "merge"] for c in self.calls()), 1)

    def test_launch_review_integrate_finish_cleanup_retry(self):
        self.start(partial=True)
        self.assertEqual(sum(c[:2] == ["workmux", "add"] for c in self.calls()), 1)
        self.command("integrate.py", *self.review)
        # Unknown artifacts are preserved, but their cleanup remains visible after done.
        unknown = self.worker / "unknown-artifact"
        unknown.write_text("retain")
        first = self.finish()
        self.assertTrue(first["pending_cleanup"])
        self.assertTrue(unknown.exists())
        inspected = self.command("finish_worker.py", "APP-TEST", "--inspect")
        self.assertTrue(inspected["saved_finish"]["pending_cleanup"])
        unknown.unlink()  # Explicit test-owner actions, not automatic cleanup.
        retried = self.command("finish_worker.py", "APP-TEST")
        self.assertTrue(retried["task_complete"])
        self.assertEqual(retried["pending_cleanup"], [])
        self.assertFalse(self.worker.exists())

    def test_interrupted_integration_reconciles_without_second_merge(self):
        self.start()
        self.env["MERGE_FAILURE"] = "after"
        self.command("integrate.py", *self.review, ok=False)
        self.env["MERGE_FAILURE"] = ""
        self.command("integrate.py", *self.review, "--reconcile")
        self.assertEqual(sum(c[:2] == ["workmux", "merge"] for c in self.calls()), 1)
        self.finish()

    def test_uncertain_exit_blocks_completion_after_integration(self):
        self.start()
        self.command("integrate.py", *self.review)
        self.env["UNCERTAIN_EXIT"] = "1"
        result = self.command(
            "finish_worker.py", "APP-TEST", "--authorize-finish", ok=False
        )
        self.assertFalse(result["task_complete"])
        self.assertFalse(result["delivered"])
        self.assertTrue(self.worker.exists())
        self.assertFalse(any(c[:2] == ["aven", "edit"] for c in self.calls()))

    def test_merge_failure_preserves_unintegrated_worker(self):
        self.start()
        self.env["MERGE_FAILURE"] = "before"
        self.command("integrate.py", *self.review, ok=False)
        self.command("integrate.py", *self.review, "--reconcile", ok=False)
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
            ("dispatch_cli.py", ["report"]),
            ("dispatch_cli.py", ["discover"]),
            ("integrate.py", []),
            ("finish_worker.py", []),
            ("verify_base.py", []),
        ):
            result = subprocess.run(
                [sys.executable, str(launch.SCRIPTS / script), *extra, "--help"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("usage:", result.stdout)
