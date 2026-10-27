import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class LaunchTests(unittest.TestCase):
    def test_documented_wrapper(self):
        runtime = (Path(__file__).parents[1] / "runtime.md").read_text()
        launch = runtime.split("Launch only once:\n\n```sh\n", 1)[1].split("\n```", 1)[
            0
        ]
        for rc in (0, 7):
            with self.subTest(rc=rc), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                attempt = root / "attempt with spaces"
                attempt.mkdir()
                skill = root / "skill with spaces"
                scripts = skill / "scripts"
                scripts.mkdir(parents=True)
                (scripts / "launch_worker.sh").write_text(
                    (Path(__file__).parents[1] / "scripts/launch_worker.sh").read_text()
                )
                binary = root / "bin"
                binary.mkdir()
                pi = binary / "pi"
                pi.write_text(
                    '#!/bin/bash\nprintf "%s\\n" "$@" > "$attempt/pi.args"\n'
                    'exit "$PI_RC"\n'
                )
                pi.chmod(0o755)
                env = dict(
                    os.environ,
                    PATH=f"{binary}:{os.environ['PATH']}",
                    PI_RC=str(rc),
                    TUIOS_SESSION="original-session",
                    TUIOS_PANE_ID="worker-pane",
                    attempt=str(attempt),
                    session="original-session",
                    workspace_name="Task with spaces",
                    workspace="3",
                    worktree=str(root),
                    cid="owned-container",
                    skill=str(skill),
                )
                # Run the documented script call with no live resources.
                prelude = r"""
set -euo pipefail
tuios() {
    case "$1" in
        list-windows) echo '{"windows":[]}' ;;
        new-window)
            [ "$2" = -s ] && [ "$3" = "$session" ] &&
                [ "$4" = "$workspace_name" ] || return 99
            while [ "$1" != -- ]; do shift; done
            shift
            "$@" || :
            echo worker-pane
            ;;
        set-agent-state)
            printf '%s\n' "$#" "$@" >> "$attempt/states"
            ;;
        *) return 99 ;;
    esac
}
python3() {
    [ "$1" = "$skill/scripts/create_container.py" ] &&
        [ "$2" = --attempt ] && [ "$3" = "$attempt" ] &&
        [ "$4" = --launch ] || return 99
    pi --session "$attempt/pi.jsonl" --tui-mode regular -- "@$attempt/prompt.md"
}
export -f tuios python3
"""
                result = subprocess.run(
                    ["bash", "-c", prelude + launch],
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(
                    (attempt / "pi.args").read_text().splitlines(),
                    [
                        "--session",
                        str(attempt / "pi.jsonl"),
                        "--tui-mode",
                        "regular",
                        "--",
                        f"@{attempt / 'prompt.md'}",
                    ],
                )
                self.assertEqual((attempt / "pi.started").read_bytes(), b"started\n")
                self.assertEqual((attempt / "pi.exit").read_bytes(), f"{rc}\n".encode())
                self.assertFalse((attempt / "pi.exit.tmp").exists())
                self.assertEqual(
                    (attempt / "worker-pane-id").read_text(), "worker-pane\n"
                )
                calls = (attempt / "states").read_text().splitlines()
                expected = []
                for state, message in (
                    ("working", "pi worker running"),
                    (
                        "done" if rc == 0 else "errored",
                        "pi exited; dispatcher review required"
                        if rc == 0
                        else f"pi execution failed: {rc}",
                    ),
                ):
                    args = [
                        "set-agent-state",
                        state,
                        "-s",
                        "original-session",
                        "-w",
                        "worker-pane",
                        "--harness",
                        "pi",
                        "-m",
                        message,
                    ]
                    expected.extend([str(len(args)), *args])
                self.assertEqual(calls, expected)
                retry = subprocess.run(
                    ["bash", "-c", prelude + launch],
                    env=env,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(retry.returncode, 0)
                self.assertEqual(
                    (attempt / "states").read_text().splitlines(), expected
                )

    def test_session_mismatch_does_not_launch(self):
        script = Path(__file__).parents[1] / "scripts/launch_worker.sh"
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["bash", str(script), "other-session", "3", "task", tmp, tmp],
                env=dict(os.environ, TUIOS_SESSION="original-session"),
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Session mismatch", result.stderr)
            self.assertFalse((Path(tmp) / "panes-before.json").exists())
