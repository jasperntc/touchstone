"""The admission gates, as tests rather than as prose in a readme.

The README says a skill directory without a `RESULT.md` fails CI. Until this
file existed that was a promise, not a mechanism, and the whole point of this
repository is the difference between the two.

`skills/` is empty today, so `test_every_skill_names_its_run` passes without
asserting anything. That is why `test_the_gate_can_say_no` is here: it builds a
synthetic skill with no result and requires the gate to reject it. A gate that
has never said no is not known to work -- the description-proposal gate in
agency-agents passed both of its keyword-stuffed decoys on the first attempt.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / "skills"


def unproven(skills_root: Path):
    """Skill directories that do not name a blind run they won."""
    if not skills_root.is_dir():
        return []
    bad = []
    for entry in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        result = entry / "RESULT.md"
        if not result.exists():
            bad.append((entry.name, "no RESULT.md"))
            continue
        text = result.read_text(encoding="utf-8")
        if not any(k in text for k in ("oracle", "none", "lift")):
            bad.append((entry.name, "RESULT.md names no comparison"))
    return bad


class Gates(unittest.TestCase):
    def test_every_skill_names_its_run(self):
        self.assertEqual(
            [], unproven(SKILLS),
            "a skill is in the tree without a RESULT.md naming the blind run "
            "it beat a control in")

    def test_the_gate_can_say_no(self):
        with tempfile.TemporaryDirectory(prefix="touchstone-gate-") as tmp:
            root = Path(tmp) / "skills"
            (root / "confident-but-unmeasured").mkdir(parents=True)
            (root / "confident-but-unmeasured" / "SKILL.md").write_text(
                "# Does great things\n", encoding="utf-8")
            self.assertEqual(
                [("confident-but-unmeasured", "no RESULT.md")], unproven(root))

            proven = root / "measured"
            proven.mkdir()
            (proven / "RESULT.md").write_text(
                "beat `none` by a lift of +30\n", encoding="utf-8")
            self.assertNotIn("measured", [n for n, _ in unproven(root)])

    def test_a_result_that_names_no_comparison_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="touchstone-gate-") as tmp:
            root = Path(tmp) / "skills"
            (root / "vague").mkdir(parents=True)
            (root / "vague" / "RESULT.md").write_text(
                "This skill works really well.\n", encoding="utf-8")
            self.assertEqual(
                [("vague", "RESULT.md names no comparison")], unproven(root))


if __name__ == "__main__":
    unittest.main(verbosity=2)
