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

import shutil
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


KEY = REPO_ROOT / "eval" / "tasks" / "key"


def _key_files():
    """Every grading key, retired ones included. Read, never imported."""
    return sorted(p for p in KEY.rglob("*")
                  if p.is_file() and "__pycache__" not in p.parts)


def _key_check_names():
    """The check functions the keys define: `check_c8_newest_first` and so on."""
    import ast
    names = set()
    for p in _key_files():
        if p.suffix == ".py":
            tree = ast.parse(p.read_text(encoding="utf-8"))
            names.update(n.name for n in ast.walk(tree)
                         if isinstance(n, ast.FunctionDef)
                         and n.name.startswith("check_"))
    return names


def _leaks(tree: Path):
    """Everything in `tree` a blind answerer could use to reach the answers."""
    import hashlib
    key_hashes = {hashlib.sha256(p.read_bytes()).hexdigest(): p.name
                  for p in _key_files()}
    key_names = {p.name.lower() for p in _key_files()}
    checks = _key_check_names()
    found = []
    for p in sorted(tree.rglob("*")):
        rel = p.relative_to(tree)
        parts = [part.lower() for part in rel.parts]
        if ".git" in parts:
            found.append("{}: .git".format(rel.as_posix()))
            continue
        if "key" in parts:
            found.append("{}: key/ path".format(rel.as_posix()))
        if not p.is_file():
            continue
        if p.name.lower() in key_names:
            found.append("{}: key file name".format(rel.as_posix()))
        data = p.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest in key_hashes:
            found.append("{}: copy of key {}".format(rel.as_posix(),
                                                     key_hashes[digest]))
        text = data.decode("utf-8", errors="replace")
        for name in sorted(checks):
            if name in text:
                found.append("{}: names {}".format(rel.as_posix(), name))
    return found


class AnswerKeyIsolation(unittest.TestCase):
    """A blind subagent gets the staged tree. Nothing in it leads to the key."""

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="touchstone-keytest-")
        cls.staged = staging.stage(Path(cls._tmp.name) / "fixture")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_key_is_there_to_compare_against(self):
        # If the key moved, every check below would pass against nothing.
        self.assertGreaterEqual(len(_key_files()), 3)
        self.assertIn("check_c8_newest_first", _key_check_names())

    def test_no_git_entry_anywhere_in_the_staged_tree(self):
        gits = [p for p in self.staged.rglob("*") if p.name.lower() == ".git"]
        self.assertEqual([], gits)

    def test_no_git_entry_above_the_staged_tree(self):
        above = [d for d in self.staged.parents if (d / ".git").exists()]
        self.assertEqual([], above, "git walking upward would find these")
        self.assertIsNone(staging._git_toplevel(self.staged))

    def test_nothing_from_the_key_was_staged(self):
        self.assertEqual([], _leaks(self.staged))

    def test_the_leak_checks_are_not_vacuous(self):
        """Plant what must never be there, and make sure it is seen."""
        with tempfile.TemporaryDirectory(prefix="touchstone-planted-") as tmp:
            planted = Path(tmp) / "fixture"
            shutil.copytree(str(self.staged), str(planted))
            self.assertEqual([], _leaks(planted))
            key = _key_files()[0]
            # A key under its own name in a key/ directory, a renamed copy, and
            # a .git directory.
            (planted / "key").mkdir()
            shutil.copy(str(key), str(planted / "key" / key.name))
            shutil.copy(str(key), str(planted / "meridian" / "helpers_copy.py"))
            (planted / ".git").mkdir()

            found = _leaks(planted)
            self.assertTrue(any("key/ path" in f for f in found), found)
            self.assertTrue(any(f.startswith("meridian/helpers_copy.py: copy of key")
                                for f in found), found)
            self.assertTrue(any(f.startswith("meridian/helpers_copy.py: names check_")
                                for f in found), found)
            self.assertTrue(any(f == ".git: .git" for f in found), found)

            problems = staging.verify(planted)
            self.assertTrue(any("grading key" in p for p in problems), problems)
            self.assertTrue(any(p.startswith(".git/") for p in problems), problems)


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
