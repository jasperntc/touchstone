"""The F002 blindness breach, written down as tests that fail without the fix.

`none/q4m` recovered the conventions with `git show` and reported doing so. The
condition is defined by not having them, so that sample was not a control and
the procedure that produced it was not blind.

`test_the_hole_is_real` is unusual and deliberate: it asserts that the
conventions ARE retrievable from this repository's history. It is not testing
`stage.py`; it is testing the premise, so that if the file is ever expunged and
the breach becomes hypothetical, this test fails loudly and someone re-reads
why the rest of the file exists rather than deleting it as paranoia.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "eval" / "harness"))

import stage as staging  # noqa: E402


class TheBreach(unittest.TestCase):
    def test_the_hole_is_real(self):
        """The conventions are in git history, so a working tree is not blindness."""
        listing = subprocess.run(
            ["git", "log", "--all", "--pretty=%H", "--", "eval/fixture/CONVENTIONS.md"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
        shas = [s for s in listing.stdout.split() if s]
        self.assertTrue(shas, "CONVENTIONS.md has no history; premise changed")
        recovered = []
        for sha in shas:
            shown = subprocess.run(
                ["git", "show", sha + ":eval/fixture/CONVENTIONS.md"],
                cwd=str(REPO_ROOT), capture_output=True, text=True, check=False)
            recovered.append(shown.stdout.lower())
        # Every committed revision is retrievable, F001's and F002's alike.
        for text in recovered:
            self.assertIn("money is micros", text)
        self.assertTrue(
            any("newest first" in t for t in recovered),
            "a blind answerer inside this repo can `git show` c8, the one "
            "convention that carried F002's entire measured effect -- which "
            "is exactly what q4m did")


class Staging(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="touchstone-stagetest-")
        cls.staged = staging.stage(Path(cls._tmp.name) / "fixture")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_no_git_resolves_from_the_staged_tree(self):
        self.assertIsNone(
            staging._git_toplevel(self.staged),
            "git resolves from the staged fixture, so `git show` can reach a "
            "committed answer key")

    def test_conventions_did_not_travel(self):
        names = {p.name for p in self.staged.rglob("*")}
        self.assertNotIn("CONVENTIONS.md", names)
        self.assertNotIn("_build_meridian.py", names)
        self.assertNotIn(".git", names)

    def test_the_fixture_arrived(self):
        self.assertTrue((self.staged / "meridian" / "__init__.py").exists())
        modules = list(self.staged.rglob("*.py"))
        self.assertGreater(len(modules), 30, "the fixture is meant to be wide")

    def test_verify_passes_its_own_staging(self):
        self.assertEqual([], staging.verify(self.staged))


class Refusals(unittest.TestCase):
    """Each of these would have produced an F002-shaped result silently."""

    def test_staging_inside_the_repo_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            staging.stage(REPO_ROOT / "eval" / "_scratch")
        self.assertIn("F002", str(caught.exception))
        self.assertFalse((REPO_ROOT / "eval" / "_scratch").exists())

    def test_verify_catches_a_tree_that_git_can_see(self):
        """The regression itself: a fixture served from inside a repository."""
        problems = staging.verify(REPO_ROOT / "eval" / "fixture")
        self.assertTrue(
            any("git` resolves" in p for p in problems),
            "verify() did not object to a fixture sitting inside a git "
            "repository, which is the F002 breach: " + repr(problems))

    def test_verify_reports_a_missing_directory(self):
        self.assertTrue(staging.verify(REPO_ROOT / "does" / "not" / "exist"))


class ProseAudit(unittest.TestCase):
    # The four docstrings that leaked four of the ten conventions in F003.
    # Not one contains a normative word, which is why the first version of the
    # detector -- a substring list of always/never/must/convention -- reported
    # the fixture clean while the controls were quoting these back verbatim as
    # their justification.
    LEAKED = [
        ("errors.py", "Error codes. Every failure in current Meridian code is "
                      "one of these."),
        ("audit.py", "The audit decorator. Every current export wears one."),
        ("ids.py", "Identifier shapes. Every current entry point validates "
                   "through here."),
        ("clock.py", "The only source of time in current Meridian code."),
    ]

    NEUTRAL = [
        "Part of the payouts service.",
        "Pre-2024 helper, kept for the migration window.",
        "Adjustment rows. Written by the nightly import; do not edit by hand.",
        "accounts.adjustments -- recent adjustments.",
    ]

    def _flagged(self, text):
        import re
        return any(re.search(pat, text, re.I) for pat, _ in staging.PROSE_PATTERNS)

    def test_the_declarative_form_is_caught(self):
        for name, text in self.LEAKED:
            self.assertTrue(
                self._flagged(text),
                "{} states a convention and the detector does not see it: "
                "{!r}".format(name, text))

    def test_neutral_prose_is_left_alone(self):
        for text in self.NEUTRAL:
            self.assertFalse(
                self._flagged(text),
                "a detector that flags ordinary prose will be ignored: "
                "{!r}".format(text))

    def test_audit_reads_prose_and_not_code(self):
        with tempfile.TemporaryDirectory(prefix="touchstone-audit-") as tmp:
            f = Path(tmp) / "m.py"
            f.write_text(
                '"""Rows, newest first."""\n'
                'ROWS = sorted(RAW, key=lambda r: -r["at_ms"])\n',
                encoding="utf-8")
            found = staging._prose(f)
        texts = [t for _, t in found]
        self.assertEqual(1, len(texts), "expected the docstring only")
        self.assertIn("newest first", texts[0])
        self.assertNotIn("sorted", texts[0], "audit must not read code")


if __name__ == "__main__":
    unittest.main(verbosity=2)
