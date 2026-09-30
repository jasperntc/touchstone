"""The gates that sit on top of skill-creator, driven through every refusal.

skill-creator supplies the runs, the grader and the benchmark. These tests are
about the three decisions it does not make, and each case here is a real result
this project produced before the gate existed:

    ceiling      agency-agents scored 24/24 in every cell across 44 blind
                 subagents with no way to tell a useless skill from an
                 unwinnable task.
    late bar     F002 came in at +12.5 and reads as "promising" unless +15 was
                 in git first.
    one finding  F002 and F003 both produced a pooled lift near +12 in which a
                 single expectation was the entire effect.

`evaluate()` is pure so all three are testable without staging a run, which is
the point: a gate whose own failure mode is expensive to reproduce will not be
tested, and an untested gate is decoration.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "eval" / "harness"))

import prereg  # noqa: E402

SPEC = {
    "run": "T",
    "primary_threshold_points": 15.0,
    "min_discriminating_expectations": 2,
    "discriminating_gap_points": 40.0,
    "required_configurations": list(prereg.REQUIRED_CONFIGS),
}


def run(config, expectations, eval_name="e1", n=1):
    """`n` runs of one configuration, each with the same pass/fail pattern."""
    out = []
    for i in range(n):
        passed = sum(1 for v in expectations.values() if v)
        out.append({
            "eval_id": 1, "eval_name": eval_name, "configuration": config,
            "run_number": i + 1,
            "result": {"pass_rate": passed / len(expectations),
                       "passed": passed, "failed": len(expectations) - passed,
                       "total": len(expectations), "time_seconds": 1.0,
                       "tokens": 10},
            "expectations": [{"text": t, "passed": v, "evidence": ""}
                             for t, v in expectations.items()],
        })
    return out


def benchmark(*groups):
    return {"metadata": {"skill_name": "t"}, "runs": [r for g in groups for r in g]}


class Ceiling(unittest.TestCase):
    def test_an_oracle_that_cannot_beat_the_baseline_rejects_the_task(self):
        """The failure agency-agents could not see from inside."""
        perfect = {"a": True, "b": True, "c": True, "d": True}
        out = prereg.evaluate(SPEC, benchmark(
            run("without_skill", perfect, n=3),
            run("oracle", perfect, n=3),
            run("with_skill", perfect, n=3)))
        self.assertEqual("TASK REJECTED", out["verdict"])
        self.assertFalse(out["ceiling_ok"])
        self.assertEqual(0.0, out["headroom"])

    def test_a_skill_is_not_scored_against_a_ceiling(self):
        """Even a skill that beats the baseline must not read as PROVEN here."""
        out = prereg.evaluate(SPEC, benchmark(
            run("without_skill", {"a": True, "b": False}, n=2),
            run("oracle", {"a": True, "b": False}, n=2),      # no headroom
            run("with_skill", {"a": True, "b": True}, n=2)))  # beats baseline
        self.assertEqual("TASK REJECTED", out["verdict"])
        self.assertFalse(out["ok"])

    def test_a_missing_oracle_arm_is_unreadable_not_a_pass(self):
        data = benchmark(run("without_skill", {"a": False}, n=2),
                         run("with_skill", {"a": True}, n=2))
        out = prereg.evaluate(SPEC, data)
        self.assertEqual("UNREADABLE", out["verdict"])
        self.assertIn("oracle", out["missing"])


class Thresholds(unittest.TestCase):
    def test_a_lift_below_the_bar_is_not_proven(self):
        """F002's shape: close, and close is a fail when the bar came first."""
        out = prereg.evaluate(SPEC, benchmark(
            run("without_skill", dict.fromkeys("abcdefgh", True) | {"i": False, "j": False}, n=1),
            run("oracle", dict.fromkeys("abcdefghij", True), n=1),
            run("with_skill", dict.fromkeys("abcdefghi", True) | {"j": False}, n=1)))
        self.assertAlmostEqual(10.0, out["lift"])
        self.assertFalse(out["lift_ok"])
        self.assertEqual("NOT PROVEN", out["verdict"])

    def test_one_expectation_carrying_the_whole_effect_is_not_proven(self):
        """F003's shape: the lift clears the bar, one check is all of it."""
        spec = dict(SPEC, primary_threshold_points=10.0)
        none = {"a": True, "b": True, "c": True, "d": False, "e": False}
        skill = {"a": True, "b": True, "c": True, "d": True, "e": False}
        out = prereg.evaluate(spec, benchmark(
            run("without_skill", none, n=1),
            run("oracle", dict.fromkeys("abcde", True), n=1),
            run("with_skill", skill, n=1)))
        self.assertTrue(out["lift_ok"], "lift should clear the lowered bar")
        self.assertEqual(1, len(out["discriminating"]))
        self.assertFalse(out["spread_ok"])
        self.assertEqual("NOT PROVEN", out["verdict"])

    def test_a_real_effect_across_two_expectations_is_proven(self):
        none = {"a": True, "b": True, "c": False, "d": False, "e": False}
        skill = {"a": True, "b": True, "c": True, "d": True, "e": False}
        out = prereg.evaluate(SPEC, benchmark(
            run("without_skill", none, n=2),
            run("oracle", dict.fromkeys("abcde", True), n=2),
            run("with_skill", skill, n=2)))
        self.assertEqual("PROVEN", out["verdict"])
        self.assertEqual(2, len(out["discriminating"]))
        self.assertAlmostEqual(40.0, out["lift"])
        self.assertAlmostEqual(60.0, out["headroom"])
        self.assertAlmostEqual(66.67, out["captured"], places=1)


class CaptureAndHarm(unittest.TestCase):
    """The two gates F004 needs, which an absolute lift cannot express.

    When the skill's payload is information genuinely absent from the codebase,
    the oracle beats the control by construction. "Did the facts help" is not a
    question -- "did the packaged skill deliver them" is.
    """

    ABSENT = dict(SPEC, primary_threshold_points=10.0,
                  min_captured_percent=80.0, harm_eval="unrelated",
                  harm_tolerance_points=5.0)

    def test_a_skill_that_delivers_little_of_the_headroom_is_not_proven(self):
        none = {"a": True, "b": False, "c": False, "d": False, "e": False}
        skill = {"a": True, "b": True, "c": False, "d": False, "e": False}
        out = prereg.evaluate(self.ABSENT, benchmark(
            run("without_skill", none, eval_name="main", n=1),
            run("oracle", dict.fromkeys("abcde", True), eval_name="main", n=1),
            run("with_skill", skill, eval_name="main", n=1),
            run("without_skill", {"z": True}, eval_name="unrelated", n=1),
            run("with_skill", {"z": True}, eval_name="unrelated", n=1)))
        self.assertTrue(out["lift_ok"], "lift clears the absolute bar")
        self.assertAlmostEqual(25.0, out["captured"])
        self.assertFalse(out["captured_ok"])
        self.assertEqual("NOT PROVEN", out["verdict"])

    def test_a_skill_that_delivers_almost_all_of_it_is_proven(self):
        none = {"a": True, "b": False, "c": False, "d": False, "e": False}
        skill = {"a": True, "b": True, "c": True, "d": True, "e": False}
        out = prereg.evaluate(self.ABSENT, benchmark(
            run("without_skill", none, eval_name="main", n=1),
            run("oracle", dict.fromkeys("abcde", True), eval_name="main", n=1),
            run("with_skill", skill, eval_name="main", n=1),
            run("without_skill", {"z": True}, eval_name="unrelated", n=1),
            run("with_skill", {"z": True}, eval_name="unrelated", n=1)))
        self.assertAlmostEqual(75.0, out["captured"])
        self.assertFalse(out["captured_ok"], "75 is under the registered 80")
        skill["e"] = True
        out = prereg.evaluate(self.ABSENT, benchmark(
            run("without_skill", none, eval_name="main", n=1),
            run("oracle", dict.fromkeys("abcde", True), eval_name="main", n=1),
            run("with_skill", skill, eval_name="main", n=1),
            run("without_skill", {"z": True}, eval_name="unrelated", n=1),
            run("with_skill", {"z": True}, eval_name="unrelated", n=1)))
        self.assertAlmostEqual(100.0, out["captured"])
        self.assertEqual("PROVEN", out["verdict"])

    def test_a_skill_that_damages_unrelated_work_is_not_proven(self):
        """The question a collection has to answer and a single eval never asks."""
        none = {"a": True, "b": False, "c": False, "d": False, "e": False}
        skill = dict.fromkeys("abcde", True)
        out = prereg.evaluate(self.ABSENT, benchmark(
            run("without_skill", none, eval_name="main", n=1),
            run("oracle", skill, eval_name="main", n=1),
            run("with_skill", skill, eval_name="main", n=1),
            run("without_skill", {"y": True, "z": True}, eval_name="unrelated", n=1),
            run("with_skill", {"y": False, "z": False}, eval_name="unrelated", n=1)))
        # Everything the skill was written for passes. The harm gate alone
        # must be what flips the verdict.
        self.assertTrue(out["lift_ok"])
        self.assertTrue(out["spread_ok"])
        self.assertTrue(out["captured_ok"])
        self.assertFalse(out["harm_ok"], "installing it wrecked an unrelated task")
        self.assertAlmostEqual(-100.0, out["harm_delta"])
        self.assertEqual("NOT PROVEN", out["verdict"])

    def test_the_harm_eval_is_held_out_of_the_primary_numbers(self):
        """A dismal unrelated eval must not drag the thing being measured."""
        none = {"a": True, "b": False}
        skill = {"a": True, "b": True}
        floor = {"z": False}
        out = prereg.evaluate(self.ABSENT, benchmark(
            run("without_skill", none, eval_name="main", n=1),
            run("oracle", skill, eval_name="main", n=1),
            run("with_skill", skill, eval_name="main", n=1),
            run("without_skill", floor, eval_name="unrelated", n=1),
            run("with_skill", floor, eval_name="unrelated", n=1)))
        self.assertAlmostEqual(50.0, out["stats"]["without_skill"]["pooled"],
                               msg="the unrelated eval leaked into the primary pool")
        self.assertAlmostEqual(50.0, out["lift"])
        self.assertTrue(out["harm_ok"])

    def test_a_declared_harm_eval_that_never_ran_is_not_proven(self):
        # Two discriminating expectations and full capture, so every other gate
        # passes: an earlier version of this test cleared on `spread` instead
        # and would have gone green with the harm gate deleted.
        none = {"a": True, "b": False, "c": False}
        skill = {"a": True, "b": True, "c": True}
        out = prereg.evaluate(self.ABSENT, benchmark(
            run("without_skill", none, eval_name="main", n=1),
            run("oracle", skill, eval_name="main", n=1),
            run("with_skill", skill, eval_name="main", n=1)))
        self.assertTrue(out["lift_ok"])
        self.assertTrue(out["spread_ok"])
        self.assertTrue(out["captured_ok"])
        self.assertFalse(out["harm_ok"], "an unrun harm check is an untested claim")
        self.assertEqual("NOT PROVEN", out["verdict"])


class Registration(unittest.TestCase):
    """The bar has to be in git, unmodified, and older than the numbers."""

    def test_an_unregistered_run_is_refused(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            bench = Path(f.name)
        try:
            problems = prereg.registration_problems("no-such-run-id", bench)
            self.assertTrue(problems)
            self.assertIn("does not exist", problems[0])
        finally:
            bench.unlink()


class RegistrationInARealRepo(unittest.TestCase):
    """The precedence check, exercised against actual git commits.

    The unit test above only covers an untracked file. This is the case that
    matters: a threshold committed AFTER the numbers were in. It needs real
    commits with real timestamps, so it builds a throwaway repository.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="touchstone-prereg-")
        self.root = Path(self._tmp.name)
        for cmd in (["init", "-q"], ["config", "user.email", "t@t"],
                    ["config", "user.name", "t"]):
            subprocess.run(["git"] + cmd, cwd=str(self.root), check=True,
                           capture_output=True)
        (self.root / "eval" / "prereg").mkdir(parents=True)
        self._saved = (prereg.REPO_ROOT, prereg.PREREG)
        prereg.REPO_ROOT = self.root
        prereg.PREREG = self.root / "eval" / "prereg"

    def tearDown(self):
        prereg.REPO_ROOT, prereg.PREREG = self._saved
        self._tmp.cleanup()

    def _commit(self, name, when):
        path = prereg.PREREG / (name + ".json")
        path.write_text(json.dumps(SPEC) + chr(10), encoding="utf-8", newline=chr(10))
        env = {"GIT_AUTHOR_DATE": str(when), "GIT_COMMITTER_DATE": str(when)}
        import os
        e = dict(os.environ, **env)
        subprocess.run(["git", "add", "-A"], cwd=str(self.root), check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", "prereg"], cwd=str(self.root),
                       check=True, capture_output=True, env=e)
        return path

    def _benchmark(self, when):
        import os
        b = self.root / "benchmark.json"
        b.write_text("{}", encoding="utf-8")
        os.utime(b, (when, when))
        return b

    def test_an_uncommitted_registration_is_refused(self):
        # This used to write into the real eval/prereg/ and delete the file
        # afterwards. The record is read-only, so it runs here instead.
        path = prereg.PREREG / "UNCOMMITTED_TEST.json"
        path.write_text(json.dumps(SPEC) + chr(10), encoding="utf-8", newline=chr(10))
        bench = self._benchmark(1_700_009_999)
        problems = prereg.registration_problems("UNCOMMITTED_TEST", bench)
        self.assertTrue(problems, "an untracked threshold fixes nothing")
        self.assertIn("not tracked", problems[0])

    def test_a_threshold_committed_before_the_run_is_accepted(self):
        self._commit("EARLY", 1_700_000_000)
        bench = self._benchmark(1_700_009_999)
        self.assertEqual([], prereg.registration_problems("EARLY", bench))

    def test_a_threshold_committed_after_the_numbers_is_refused(self):
        """The whole reason this file exists."""
        self._commit("LATE", 1_700_009_999)
        bench = self._benchmark(1_700_000_000)
        problems = prereg.registration_problems("LATE", bench)
        self.assertTrue(problems, "a bar set after the numbers was accepted")
        self.assertIn("not a threshold", problems[0])

    def test_editing_a_committed_threshold_is_refused(self):
        path = self._commit("EDITED", 1_700_000_000)
        bench = self._benchmark(1_700_009_999)
        self.assertEqual([], prereg.registration_problems("EDITED", bench))
        moved = dict(SPEC, primary_threshold_points=1.0)
        path.write_text(json.dumps(moved) + chr(10), encoding="utf-8", newline=chr(10))
        problems = prereg.registration_problems("EDITED", bench)
        self.assertTrue(problems, "the bar was moved on disk and went unnoticed")
        self.assertIn("differs from HEAD", problems[0])


class AdapterHarmSplit(unittest.TestCase):
    """The adapter must learn which eval is held out, never assume it.

    F005 was first scored with `is_harm = task["task"] != "t004"` hardcoded.
    t004 had been retired and replaced by t005, so EVERY task matched, the
    primary eval was emitted with all nine checks pooled instead of the three
    absent ones, and a +100 absent lift was diluted to +33.3 -- failing a +40
    bar that had been pre-registered against the absent checks specifically.
    The verdict flipped on a hardcoded string.
    """

    def setUp(self):
        sys.path.insert(0, str(REPO_ROOT / "eval" / "harness"))
        import to_benchmark
        self.mod = to_benchmark

    def test_an_unknown_harm_eval_is_refused(self):
        with self.assertRaises(SystemExit) as caught:
            self.mod.build(REPO_ROOT, {}, REPO_ROOT / "x.json", "t999")
        self.assertIn("not in tasks.jsonl", str(caught.exception))

    def test_the_harm_eval_comes_from_the_registration(self):
        spec = json.loads(
            (prereg.PREREG / "F005.json").read_text(encoding="utf-8"))
        self.assertTrue(spec.get("harm_eval"),
                        "the registration must name the held-out eval")
        tasks = {t["task"] for t in __import__("run_checks").load_tasks()}
        self.assertIn(spec["harm_eval"], tasks)
        self.assertGreater(len(tasks), 1, "no held-out eval means no harm gate")

    def test_no_task_id_is_compared_in_the_adapter(self):
        """Prose may name t004; a COMPARISON against a task id may not.

        The first version of this test flagged every mention including the
        docstrings that explain the bug, which would have forced deleting the
        explanation to make the test pass. It looks for the bug's actual
        shape instead: a task id on either side of == or !=.
        """
        import ast
        src = (REPO_ROOT / "eval" / "harness" / "to_benchmark.py").read_text(
            encoding="utf-8")
        offenders = []
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.Compare):
                continue
            for side in [node.left] + list(node.comparators):
                if (isinstance(side, ast.Constant)
                        and isinstance(side.value, str)
                        and side.value.startswith("t0")):
                    offenders.append(side.value)
        self.assertEqual([], offenders,
                         "a task id is compared in adapter logic again")


class Prompts(unittest.TestCase):
    def test_arms_differing_only_by_the_treatment_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "base.txt").write_text("do the task\n\nreport back\n", encoding="utf-8")
            (d / "block.txt").write_text("HERE ARE THE RULES\n\n", encoding="utf-8")
            (d / "treated.txt").write_text(
                "do the task\n\nHERE ARE THE RULES\n\nreport back\n", encoding="utf-8")
            self.assertEqual(0, prereg.check_prompts(
                d / "base.txt", d / "treated.txt", d / "block.txt"))

    def test_any_other_difference_is_caught(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "base.txt").write_text("do the task\n\nreport back\n", encoding="utf-8")
            (d / "block.txt").write_text("HERE ARE THE RULES\n\n", encoding="utf-8")
            # "carefully" is the uncontrolled variable.
            (d / "treated.txt").write_text(
                "do the task carefully\n\nHERE ARE THE RULES\n\nreport back\n",
                encoding="utf-8")
            self.assertEqual(1, prereg.check_prompts(
                d / "base.txt", d / "treated.txt", d / "block.txt"))


class SkillCreatorCompatibility(unittest.TestCase):
    """Read the real schema, not one invented here."""

    SCHEMA = Path.home() / ".claude" / "plugins" / "marketplaces" / \
        "claude-plugins-official" / "plugins" / "skill-creator" / "skills" / \
        "skill-creator" / "references" / "schemas.md"

    def test_the_fields_this_gate_reads_are_the_documented_ones(self):
        if not self.SCHEMA.exists():
            self.skipTest("skill-creator plugin not installed")
        text = self.SCHEMA.read_text(encoding="utf-8")
        for field in ('"configuration"', '"eval_name"', '"pass_rate"',
                      '"passed"', '"total"', '"expectations"', '"text"'):
            self.assertIn(field, text,
                          "{} is not in skill-creator's schema; this gate would "
                          "read a field that does not exist".format(field))


if __name__ == "__main__":
    unittest.main(verbosity=2)
