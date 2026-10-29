"""Tests for the behavioural evals' fixture in evals/. Run: python3 -m unittest discover -s tests

Each eval case starts from the vault its scaffold.sh sets up. These tests run every scaffold the
way `claude plugin eval --scaffold` does, in an empty workspace with a temporary HOME, and check
what the cases rely on: a vault the script finds sound, and file graders that judge an untouched
vault the way each case expects."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS = ROOT / "evals"
sys.path.insert(0, str(ROOT / "skills" / "study" / "scripts"))
import appledore  # noqa: E402

CASES = sorted(p.parent for p in EVALS.glob("*/case.yaml"))


def case_field(case, pattern):
    """One field of a case.yaml, by a regex with one group; the files are plain enough for that."""
    m = re.search(pattern, (case / "case.yaml").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def grader(path):
    """A grader file's frontmatter, as flat key-value strings, and its body."""
    _, fm, body = path.read_text(encoding="utf-8").split("---\n", 2)
    keys = dict(line.split(":", 1) for line in fm.splitlines() if ":" in line)
    return {k.strip(): v.strip() for k, v in keys.items()}, body.strip()


@unittest.skipUnless(shutil.which("bash"), "the scaffolds need bash")
class EvalFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.workspaces = {}
        for case in CASES:
            home = Path(cls.tmp.name) / case.name / "home"
            workspace = home / "cwd"
            workspace.mkdir(parents=True)
            subprocess.run(["bash", str(case / "scaffold.sh")], cwd=workspace, check=True,
                           capture_output=True, env={**os.environ, "HOME": str(home)})
            cls.workspaces[case.name] = workspace

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_scaffold_sets_up_a_sound_vault(self):
        # A warning in the fixture gives the agent something to fix that no case asked for.
        for name, workspace in self.workspaces.items():
            with self.subTest(case=name):
                errors, warnings = appledore.check(appledore.Vault(workspace / "vault"))
                self.assertEqual([], errors)
                self.assertEqual([], warnings)

    def test_freshness_is_two_words_under_the_limit(self):
        # Case 05 files an answer into Freshness, so it must go past the 450 words a subtopic may have.
        vault = appledore.Vault(self.workspaces["05-oversized-subtopic-splits"] / "vault")
        self.assertEqual(448, vault.get("Freshness").words())

    def test_file_graders_judge_an_untouched_vault_as_designed(self):
        """A regex grader on a file passes on the untouched workspace in a read-only case, so its pass
        means the session left the file alone, and fails in a case that must write, so its pass means
        the session did the work."""
        for case in CASES:
            read_only = "read-only" in (case_field(case, r"^tags:\s*\[([^\]]*)\]") or "")
            for path in sorted((case / "graders").glob("*.md")):
                keys, pattern = grader(path)
                target = re.search(r'path:\s*"([^"]+)"', keys.get("target", ""))
                if keys.get("type") != "regex" or not target:
                    continue
                with self.subTest(grader=f"{case.name}/{path.stem}"):
                    file = self.workspaces[case.name] / target.group(1)
                    flags = (re.M if "m" in keys.get("flags", "") else 0) | (re.I if "i" in keys.get("flags", "") else 0)
                    found = file.exists() and re.search(pattern, file.read_text(encoding="utf-8"), flags) is not None
                    self.assertEqual(read_only, not found if keys.get("match") == "not_contains" else found)

    def test_source_pages_name_no_other_document(self):
        # Case 04 fails an answer that cites another document, and a page that says it belongs to
        # an eval can change how the agent behaves.
        for page in sorted((EVALS / "_fixture" / "sources").glob("*.md")):
            with self.subTest(page=page.name):
                text = page.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"\bRFC\b|Cloudflare|Fastly|Akamai|CloudFront")
                self.assertNotRegex(text, r"(?i)\bevals?\b")

    def test_history_files_are_one_chain_ending_on_a_reply(self):
        # The runner resumes the transcript, and the case's prompt becomes the next user turn. A
        # resumed run also writes its own transcript beside it, with the operator's real paths: git
        # ignores it, and this test fails until it is deleted.
        for case in CASES:
            name = case_field(case, r"^\s+history_file:\s*(\S+)")
            stray = sorted(p.name for p in case.glob("*.jsonl") if p.name != name)
            self.assertEqual([], stray, f"{case.name}: transcripts its case.yaml doesn't name; delete them")
            if not name:
                continue
            with self.subTest(case=case.name):
                lines = [json.loads(line) for line in (case / name).read_text(encoding="utf-8").splitlines()]
                self.assertEqual(["user", "assistant"] * (len(lines) // 2), [line["type"] for line in lines])
                self.assertEqual([None] + [line["uuid"] for line in lines[:-1]], [line["parentUuid"] for line in lines])
                self.assertEqual(1, len({line["sessionId"] for line in lines}))


if __name__ == "__main__":
    unittest.main()
