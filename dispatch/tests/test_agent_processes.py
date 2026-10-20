"""Linux process evidence: actual argv/executable and exact guest cwd, not config."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/agent_processes.py"
SPEC = importlib.util.spec_from_file_location("agent_processes", SCRIPT)
PROBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROBE)


class AgentProcessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.proc = Path(self.temp.name)

    def process(self, pid, argv, cwd="/guest/worker", exe="/usr/bin/node", state="S"):
        path = self.proc / str(pid)
        path.mkdir()
        (path / "cwd").symlink_to(cwd)
        (path / "exe").symlink_to(exe)
        (path / "cmdline").write_bytes("\0".join(argv).encode() + b"\0")
        fields = [state, *(["0"] * 18), "12345"]
        (path / "stat").write_text(f"{pid} (pi with spaces) " + " ".join(fields))
        return path

    def test_pi_process_title_and_exact_identity(self):
        self.process(3, ["pi", "", ""])
        observed = PROBE.observe("/guest/worker", self.proc)
        self.assertEqual(
            observed,
            [
                {
                    "pid": 3,
                    "start_ticks": "12345",
                    "exe": "/usr/bin/node",
                    "argv": ["pi"],
                    "cwd": "/guest/worker",
                    "kind": "pi",
                }
            ],
        )

    def test_node_entrypoint_is_recognized_without_agent_config(self):
        self.process(
            3,
            [
                "node",
                "/opt/node_modules/@earendil-works/pi-coding-agent/dist/cli.js",
                "prompt",
            ],
        )
        self.assertEqual(len(PROBE.observe("/guest/worker", self.proc)), 1)

    def test_wrong_cwd_shell_text_unknown_executable_and_zombie_are_not_evidence(self):
        self.process(3, ["pi"], cwd="/different/worker")
        self.process(4, ["sh", "-c", "pi prompt"], exe="/bin/sh")
        self.process(5, ["node", "/tmp/pi-coding-agent/dist/cli.js"])
        self.process(6, ["pi"], exe="/bin/echo")
        self.process(7, ["pi"], state="Z")
        self.assertEqual(PROBE.observe("/guest/worker", self.proc), [])

    def test_ambiguity_is_preserved_for_the_caller(self):
        self.process(3, ["pi"])
        self.process(4, ["pi"])
        self.assertEqual(len(PROBE.observe("/guest/worker", self.proc)), 2)

    def test_exited_process_is_not_live_proof(self):
        path = self.process(3, ["pi"])
        (path / "stat").unlink()
        self.assertEqual(PROBE.observe("/guest/worker", self.proc), [])


if __name__ == "__main__":
    unittest.main()
