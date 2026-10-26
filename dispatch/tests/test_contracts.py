"""Local documentation and safety lint. No live workflow acceptance is claimed."""
import ast
import re
import shlex
from pathlib import Path
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def shell_blocks(text):
    return re.findall(r"```(?:sh|bash)\n(.*?)```", text, re.S)


def forbidden_commands(block):
    """Inspect direct CLI examples only, not prose or an agent's future behavior."""
    tokens = list(shlex.shlex(block, posix=True, punctuation_chars=";&|()<>"))
    bad = []
    for index, token in enumerate(tokens):
        if token != "tuios":
            continue
        tail = tokens[index + 1:]
        if not tail:
            continue
        if tail[0] in {"ask-human", "request-approval", "respond", "attach", "restart-server", "set-agent-state"}:
            bad.append(tail[0])
        if tail[0] == "ship" and len(tail) > 1 and tail[1] in {"push", "pr"}:
            bad.append("ship " + tail[1])
    return bad


def heading_ids(text):
    seen = {}
    ids = set()
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)(?:\s+#+)?$", line)
        if not match:
            continue
        title = match[1].lower().replace("`", "")
        slug = re.sub(r"[^\w\- ]", "", title).replace(" ", "-")
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        ids.add(slug if count == 0 else f"{slug}-{count}")
    return ids


class LinkTests(unittest.TestCase):
    def test_local_markdown_targets_and_fragments(self):
        # Includes assets/scripts when linked. Ignore only explicit remote schemes.
        for source in ROOT.rglob("*.md"):
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", source.read_text()):
                with self.subTest(source=str(source.relative_to(ROOT)), target=target):
                    parts = urlsplit(target)
                    if parts.scheme or parts.netloc:
                        continue
                    dest = (source.parent / unquote(parts.path)).resolve() if parts.path else source
                    self.assertTrue(dest.is_relative_to(ROOT.resolve()), "link escapes install")
                    self.assertTrue(dest.exists(), "missing local target")
                    if parts.fragment:
                        self.assertEqual(dest.suffix, ".md", "unsupported fragment target")
                        self.assertIn(unquote(parts.fragment), heading_ids(dest.read_text()))

    def test_heading_slug_duplicates(self):
        self.assertEqual(heading_ids("# Same\n## Same\n## A `test`: result"),
                         {"same", "same-1", "a-test-result"})


class SafetyTests(unittest.TestCase):
    def test_shell_examples_do_not_initiate_human_input_or_bypass(self):
        count = 0
        for path in ROOT.rglob("*.md"):
            if path.name == "PLAN.md":
                continue  # Requirements are not executable examples.
            for block in shell_blocks(path.read_text()):
                count += 1
                with self.subTest(path=str(path.relative_to(ROOT)), block=block):
                    self.assertEqual(forbidden_commands(block), [])
                    tokens = shlex.split(block, comments=True)
                    self.assertFalse(set(tokens) & {"--allow-blocked", "--force", "--focus", "--request"})
                    self.assertNotIn("respond", next((t.split("=")[-1].split(",") for t in tokens
                                                       if t.startswith("--grants=")), []))
                    for i, token in enumerate(tokens[:-1]):
                        if token == "--grants":
                            self.assertNotIn("respond", tokens[i + 1].split(","))
        self.assertGreater(count, 10, "no meaningful example coverage")

    def test_command_lint_rejects_unsafe_examples(self):
        for text in ("tuios ask-human 'input'", "tuios ship push --yes",
                     "tuios ship pr", "tuios respond 3 yes", "tuios restart-server",
                     "tuios attach work", "tuios set-agent-state done"):
            with self.subTest(text=text):
                self.assertTrue(forbidden_commands(text))
        self.assertEqual(forbidden_commands("tuios ask-agent -s work -w worker 'Review'"), [])

    def test_helper_has_no_execution_network_or_mutation_api(self):
        # AST-based import/call limits, not a keyword search through comments.
        scripts = sorted((ROOT / "scripts").glob("*.py"))
        self.assertEqual([p.name for p in scripts], ["dashboard.py"])
        allowed_imports = {"argparse", "json", "pathlib", "sys", "xml.sax.saxutils"}
        banned_calls = {"eval", "exec", "__import__", "getattr", "setattr", "open",
                        "system", "popen", "run", "Popen", "spawn", "fork", "execv",
                        "write_text", "write_bytes", "unlink", "rename", "replace_file",
                        "mkdir", "rmdir", "connect", "urlopen", "sleep"}
        for path in scripts:
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue({a.name for a in node.names} <= allowed_imports)
                if isinstance(node, ast.ImportFrom):
                    self.assertIn(node.module, allowed_imports)
                if isinstance(node, ast.Call):
                    name = (node.func.id if isinstance(node.func, ast.Name) else
                            node.func.attr if isinstance(node.func, ast.Attribute) else "")
                    self.assertNotIn(name, banned_calls)
                self.assertNotIsInstance(node, (ast.AsyncFunctionDef, ast.Await))


class CoverageTests(unittest.TestCase):
    def test_release_checks_distinguish_live_from_static(self):
        doc = (ROOT / "references/acceptance.md").read_text()
        for exercise in ("Native lifecycle", "Linux execution", "Busy worker",
                         "Agent communication", "Competing attempts", "Recovery",
                         "Dashboard", "Workspace", "No human input"):
            self.assertIn("| " + exercise + " |", doc)
        self.assertTrue((ROOT / "references/verification.md").is_file())
        self.assertIn("Static tests are not live acceptance.", (ROOT / "README.md").read_text())

    def test_operating_guides_stay_bounded(self):
        # Prevent the former sprawling procedure from returning.
        self.assertLessEqual(len((ROOT / "SKILL.md").read_text().splitlines()), 85)
        for path in (ROOT / "references").glob("*.md"):
            if path.name != "verification.md":
                with self.subTest(path=path.name):
                    self.assertLessEqual(len(path.read_text().splitlines()), 120)

    def test_linux_and_pane_lifecycle_have_native_procedures(self):
        workers = (ROOT / "references/workers.md").read_text()
        execution = (ROOT / "references/pi.md").read_text()
        checks = (ROOT / "references/review-delivery.md").read_text()
        self.assertIn("pane-view", workers)
        self.assertIn("starter shell", workers)
        self.assertIn('worktree pull "$REMOTE_SESSION"', execution)
        self.assertIn("--all-hosts", execution)
        self.assertIn("GIT_PAGER=cat PAGER=cat", checks)
        self.assertIn('close-window -s "$SESSION" checks', checks)

    def test_readme_is_short_and_skill_is_installable(self):
        self.assertLessEqual(len((ROOT / "README.md").read_text().splitlines()), 70)
        skill = (ROOT / "SKILL.md").read_text()
        self.assertTrue(skill.startswith("---\nname: dispatch\n"))
        self.assertTrue((ROOT / "assets/dashboard.tml").is_file())
        self.assertTrue((ROOT / "assets/dashboard-example.json").is_file())


if __name__ == "__main__":
    unittest.main()
