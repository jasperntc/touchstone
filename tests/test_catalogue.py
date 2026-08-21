"""The evidence labels, and the matcher that got them wrong first.

`--check` caught a real bug on its first execution: `classify()` matched with
`in` rather than a prefix, so every marketplace skill was labelled
`proven-here` -- all 31 of them -- because their paths contain "/skills/" and
that was the first rule.

That is the third loose matcher this project has shipped. The proposal gate in
agency-agents counted adjacent phrases and passed both keyword-stuffed decoys.
The prose detector matched normative words and could not see "Every current
entry point validates through here". Each was written against the cases its
author had in mind and tested only on those. So the first test here is the
collision, not the happy path.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import catalogue  # noqa: E402


class Matching(unittest.TestCase):
    def setUp(self):
        self.sources = catalogue.load_sources()

    def test_a_marketplace_path_is_not_one_of_our_skills(self):
        """The bug: every marketplace path contains '/skills/'."""
        rule = catalogue.classify(
            "marketplaces/claude-plugins-official/plugins/plugin-dev/skills/"
            "skill-development/SKILL.md", self.sources)
        self.assertEqual("shipped-unmeasured", rule["status"])
        self.assertNotEqual(
            "proven-here", rule["status"],
            "a substring matcher labels other people's work as ours")

    def test_our_own_shelves_classify_by_prefix(self):
        self.assertEqual("proven-here",
                         catalogue.classify("skills/", self.sources)["status"])
        self.assertEqual("unproven",
                         catalogue.classify("candidates/", self.sources)["status"])
        self.assertEqual("measured-no-effect",
                         catalogue.classify("quarry/", self.sources)["status"])

    def test_an_unrecognised_source_is_unproven_by_default(self):
        rule = catalogue.classify("somewhere/else/", self.sources)
        self.assertEqual("unproven", rule["status"])
        self.assertFalse(rule.get("public"),
                         "an unknown source must not be published by default")

    def test_the_negative_result_is_carried_not_lost(self):
        """116 blind subagents found nothing. That belongs on the label."""
        rule = catalogue.classify("quarry/", self.sources)
        self.assertIn("116", rule["citation"])
        self.assertIn("no measurable effect", rule["citation"])


class ProvenLabel(unittest.TestCase):
    def test_check_refuses_a_proven_label_with_no_result(self):
        entries = [{"source": "skills/confident", "status": "proven-here",
                    "result": None}]
        self.assertEqual(1, catalogue.check(entries))

    def test_check_refuses_a_result_that_names_no_control(self):
        entries = [{"source": "skills/vague", "status": "proven-here",
                    "result": {"names_a_comparison": False, "chars": 40}}]
        self.assertEqual(1, catalogue.check(entries))

    def test_check_accepts_a_result_that_names_a_control(self):
        entries = [{"source": "skills/measured", "status": "proven-here",
                    "result": {"names_a_comparison": True, "chars": 400}}]
        self.assertEqual(0, catalogue.check(entries))

    def test_an_empty_shelf_passes_and_says_so(self):
        self.assertEqual(0, catalogue.check([]))

    def test_a_result_file_is_read_for_what_it_actually_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "s"
            d.mkdir()
            self.assertIsNone(catalogue._result_figures(d))
            (d / "RESULT.md").write_text("This skill is great.\n", encoding="utf-8")
            self.assertFalse(catalogue._result_figures(d)["names_a_comparison"])
            (d / "RESULT.md").write_text(
                "F004: captured 82% of the oracle headroom over without_skill.\n",
                encoding="utf-8")
            self.assertTrue(catalogue._result_figures(d)["names_a_comparison"])


class Privacy(unittest.TestCase):
    """This repository is public; what is installed on a machine is not."""

    def test_only_public_sources_reach_the_committed_catalogue(self):
        entries = catalogue.scan()
        published = [e for e in entries if e["public"]]
        for e in published:
            self.assertNotEqual(
                "unproven", e["status"],
                "the default-deny branch leaked into the public catalogue")

    def test_the_local_catalogue_is_gitignored(self):
        ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("catalogue.local.json", ignored,
                      "a scan of installed plugins must not be committable")


class Frontmatter(unittest.TestCase):
    def test_name_and_description_are_read_including_wrapped_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "SKILL.md"
            f.write_text(
                "---\nname: thing\ndescription: does a thing\n"
                "  and keeps doing it\n---\n\n# Thing\n", encoding="utf-8")
            front = catalogue._front(f)
        self.assertEqual("thing", front["name"])
        self.assertEqual("does a thing and keeps doing it", front["description"])

    def test_a_file_with_no_frontmatter_does_not_explode(self):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "SKILL.md"
            f.write_text("# just a heading\n", encoding="utf-8")
            self.assertEqual({}, catalogue._front(f))


if __name__ == "__main__":
    unittest.main(verbosity=2)
