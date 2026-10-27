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
                root = Path(tmp)
                attempt = root / "attempt with spaces"
                attempt.mkdir()
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
                )
                # Run the documented nested Bash unchanged, with no live resources.
                prelude = r"""
set -euo pipefail
owned_state() { echo running; }
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
container() {
    [ "$1" = exec ] && [ "$2" = --interactive ] &&
        [ "$3" = --tty ] && [ "$4" = --workdir ] &&
        [ "$5" = "$worktree" ] && [ "$6" = "$cid" ] || return 99
    shift 6
    "$@"
}
export -f tuios container
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
