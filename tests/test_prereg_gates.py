"""Every gate in prereg.py, driven to its boundary and one step past it.

test_prereg.py tells the story of why each gate exists. This file is the
other half: each test pins one comparison, with every other gate set to pass,
so that inverting that comparison in prereg.py fails a test here.
test_prereg_mutants.py does the inverting and checks that something fails.

The timing cases need real commits with real timestamps. They build throwaway
repositories in temp dirs and point prereg at them. Nothing here runs prereg
against the real eval/prereg/, and the module checks on teardown that the
record was not touched.
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True   # nothing lands in eval/harness/__pycache__

import contextlib  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "eval" / "harness"))

import prereg  # noqa: E402
from tests.test_prereg import SPEC, benchmark, run  # noqa: E402

# The record, as it is on disk when this module starts.
WATCHED = [REPO_ROOT / "eval" / "prereg", REPO_ROOT / "eval" / "tasks" / "key"]
_SNAPSHOT = {}


def _hashes():
    out = {}
    for top in WATCHED:
        for p in sorted(top.rglob("*")):
            if p.is_file() and "__pycache__" not in p.parts:
                out[p.relative_to(REPO_ROOT).as_posix()] = hashlib.sha256(
                    p.read_bytes()).hexdigest()
    return out


def setUpModule():
    _SNAPSHOT.update(_hashes())


def tearDownModule():
    if _hashes() != _SNAPSHOT:
        raise AssertionError("the real record changed while these tests ran")


# ---------------------------------------------------------------- evaluate()

FIVE = "abcde"
HARM = ["h{}".format(i) for i in range(10)]


def first(k, keys=FIVE):
    """The first `k` expectations pass, the rest fail."""
    return {x: i < k for i, x in enumerate(keys)}


# Every gate passes with room to spare on the default arms below:
#   without 1/5 = 20, oracle 5/5 = 100, skill 3/5 = 60
#   headroom 80, lift 40 vs 30, spread b,c = 2 vs 2, captured 50 vs 40,
#   harm 10/10 vs 10/10 = 0 vs -10.
# All the pooled rates are k/5 or k/10 of 100, so the float arithmetic is exact
# and a boundary test sits exactly on the boundary.
GATES = dict(SPEC, primary_threshold_points=30.0, min_captured_percent=40.0,
             harm_eval="unrelated", harm_tolerance_points=10.0)


def arms(without=1, oracle=5, skill=3, harm_without=10, harm_skill=10):
    """A benchmark: main eval over a-e, harm eval `unrelated` over h0-h9.

    Pass None to leave a group out.
    """
    groups = []
    for config, k in (("without_skill", without), ("oracle", oracle),
                      ("with_skill", skill)):
        if k is not None:
            groups.append(run(config, first(k), eval_name="main"))
    for config, k in (("without_skill", harm_without), ("with_skill", harm_skill)):
        if k is not None:
            groups.append(run(config, first(k, HARM), eval_name="unrelated"))
    return benchmark(*groups)


class GateCase(unittest.TestCase):
    FLAGS = ("lift_ok", "spread_ok", "captured_ok", "harm_ok")

    def assertProven(self, out):
        self.assertTrue(out["ceiling_ok"])
        for flag in self.FLAGS:
            self.assertTrue(out[flag], flag)
        self.assertEqual("PROVEN", out["verdict"])
        self.assertTrue(out["ok"])

    def assertOnlyGateFails(self, out, gate):
        """`gate` is what stops it; every other gate passed."""
        self.assertTrue(out["ceiling_ok"])
        for flag in self.FLAGS:
            self.assertEqual(flag != gate, out[flag], flag)
        self.assertEqual("NOT PROVEN", out["verdict"])
        self.assertFalse(out["ok"])


class Baseline(GateCase):
    def test_the_default_arms_pass_every_gate(self):
        out = prereg.evaluate(GATES, arms())
        self.assertProven(out)
        self.assertAlmostEqual(80.0, out["headroom"])
        self.assertAlmostEqual(40.0, out["lift"])
        self.assertAlmostEqual(50.0, out["captured"])
        self.assertAlmostEqual(0.0, out["harm_delta"])


class OracleGate(GateCase):
    """No skill beats a ceiling, so a task without headroom is rejected."""

    def test_an_oracle_below_the_baseline_rejects_the_task(self):
        out = prereg.evaluate(GATES, arms(without=3, oracle=2, skill=5))
        self.assertLess(out["headroom"], 0)
        self.assertEqual("TASK REJECTED", out["verdict"])
        self.assertFalse(out["ceiling_ok"])
        self.assertFalse(out["ok"])

    def test_an_oracle_level_with_the_baseline_rejects_the_task(self):
        out = prereg.evaluate(GATES, arms(without=3, oracle=3, skill=5))
        self.assertEqual(0.0, out["headroom"])
        self.assertEqual("TASK REJECTED", out["verdict"])
        self.assertFalse(out["ok"])

    def test_the_smallest_headroom_is_not_rejected(self):
        # One expectation of headroom, and the skill takes all of it.
        spec = dict(GATES, primary_threshold_points=20.0,
                    min_discriminating_expectations=1)
        out = prereg.evaluate(spec, arms(without=4, oracle=5, skill=5))
        self.assertAlmostEqual(20.0, out["headroom"])
        self.assertTrue(out["ceiling_ok"])
        self.assertNotEqual("TASK REJECTED", out["verdict"])
        self.assertProven(out)

    def test_an_oracle_that_only_ran_the_harm_eval_is_not_proven(self):
        data = arms(oracle=None)
        data["runs"] += run("oracle", first(10, HARM), eval_name="unrelated")
        out = prereg.evaluate(GATES, data)
        self.assertFalse(out["ok"])
        self.assertNotEqual("PROVEN", out["verdict"])


class ThresholdCheck(GateCase):
    def test_a_lift_exactly_at_the_bar_meets_it(self):
        out = prereg.evaluate(dict(GATES, primary_threshold_points=40.0), arms())
        self.assertAlmostEqual(40.0, out["lift"])
        self.assertProven(out)

    def test_a_lift_just_under_the_bar_is_not_proven(self):
        out = prereg.evaluate(dict(GATES, primary_threshold_points=41.0), arms())
        self.assertOnlyGateFails(out, "lift_ok")

    def test_a_negative_lift_is_not_proven(self):
        out = prereg.evaluate(GATES, arms(without=2, skill=1))
        self.assertLess(out["lift"], 0)
        self.assertFalse(out["lift_ok"])
        self.assertEqual("NOT PROVEN", out["verdict"])


class SpreadGate(GateCase):
    def test_the_discriminating_expectations_are_the_ones_that_moved(self):
        out = prereg.evaluate(GATES, arms())
        self.assertEqual([("main", "b"), ("main", "c")], out["discriminating"])

    def test_exactly_the_minimum_count_meets_it(self):
        out = prereg.evaluate(dict(GATES, min_discriminating_expectations=2), arms())
        self.assertEqual(2, len(out["discriminating"]))
        self.assertProven(out)

    def test_one_fewer_than_the_minimum_is_not_proven(self):
        out = prereg.evaluate(dict(GATES, min_discriminating_expectations=3), arms())
        self.assertOnlyGateFails(out, "spread_ok")

    def test_a_gap_exactly_at_the_bar_counts(self):
        # Two skill runs, one passing b and c, one not: 50 points on each.
        data = arms(skill=None)
        data["runs"] += run("with_skill", first(3), eval_name="main")
        data["runs"] += run("with_skill", first(1), eval_name="main")
        at = prereg.evaluate(dict(GATES, discriminating_gap_points=50.0), data)
        self.assertEqual([("main", "b"), ("main", "c")], at["discriminating"])
        over = prereg.evaluate(dict(GATES, discriminating_gap_points=51.0), data)
        self.assertEqual([], over["discriminating"])


class CaptureGate(GateCase):
    def test_capture_exactly_at_the_minimum_meets_it(self):
        out = prereg.evaluate(dict(GATES, min_captured_percent=50.0), arms())
        self.assertAlmostEqual(50.0, out["captured"])
        self.assertProven(out)

    def test_capture_just_under_the_minimum_is_not_proven(self):
        out = prereg.evaluate(dict(GATES, min_captured_percent=51.0), arms())
        self.assertOnlyGateFails(out, "captured_ok")

    def test_no_minimum_means_no_capture_gate(self):
        spec = dict(GATES)
        del spec["min_captured_percent"]
        self.assertProven(prereg.evaluate(spec, arms()))
        self.assertProven(prereg.evaluate(dict(GATES, min_captured_percent=0.0),
                                          arms()))


class HarmEval(GateCase):
    def test_a_drop_exactly_at_the_tolerance_is_allowed(self):
        out = prereg.evaluate(GATES, arms(harm_skill=9))
        self.assertAlmostEqual(-10.0, out["harm_delta"])
        self.assertProven(out)

    def test_a_drop_past_the_tolerance_is_not_proven(self):
        out = prereg.evaluate(GATES, arms(harm_skill=8))
        self.assertAlmostEqual(-20.0, out["harm_delta"])
        self.assertOnlyGateFails(out, "harm_ok")

    def test_a_negative_tolerance_reads_as_its_size(self):
        spec = dict(GATES, harm_tolerance_points=-10.0)
        self.assertProven(prereg.evaluate(spec, arms(harm_skill=9)))
        self.assertOnlyGateFails(prereg.evaluate(spec, arms(harm_skill=8)),
                                 "harm_ok")

    def test_an_improvement_on_the_harm_eval_is_fine(self):
        out = prereg.evaluate(GATES, arms(harm_without=5, harm_skill=10))
        self.assertAlmostEqual(50.0, out["harm_delta"])
        self.assertProven(out)

    def test_a_harm_eval_only_the_skill_ran_is_not_proven(self):
        out = prereg.evaluate(GATES, arms(harm_without=None))
        self.assertIsNone(out["harm_delta"])
        self.assertOnlyGateFails(out, "harm_ok")

    def test_harm_expectations_never_count_toward_the_spread(self):
        # The skill wrecks the harm eval; none of that may read as movement.
        out = prereg.evaluate(GATES, arms(harm_skill=0))
        self.assertEqual({"main"}, {key[0] for key, *_ in out["rows"]})
        self.assertEqual([("main", "b"), ("main", "c")], out["discriminating"])

    def test_an_undeclared_harm_eval_is_pooled_like_any_other(self):
        out = prereg.evaluate(dict(GATES, harm_eval=""), arms())
        self.assertEqual(15, out["stats"]["without_skill"]["total"])
        self.assertIsNone(out["harm_delta"])
        self.assertTrue(out["harm_ok"])

    @unittest.expectedFailure  # evaluate() checks required arms before the harm split; see .release-prep/04-tests.md
    def test_a_control_that_only_ran_the_harm_eval_is_not_proven(self):
        # without_skill never ran the primary task. There is no control, so
        # there is no lift to measure.
        out = prereg.evaluate(GATES, arms(without=None))
        self.assertFalse(out["ok"], "PROVEN with no control on the primary task")
        self.assertNotEqual("PROVEN", out["verdict"])


# ------------------------------------------------- registration_problems()

T0 = 1_700_000_000
HOUR = 3600
_GIT_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_CEILING_DIRECTORIES",
            "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR", "GIT_NAMESPACE")


class RegistrationTiming(unittest.TestCase):
    """The bar must be committed, unchanged, and older than the numbers.

    Each test gets its own throwaway repository. prereg's REPO_ROOT and PREREG
    are patched to point at it, and every test asserts that before calling in.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="touchstone-gates-")
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name).resolve()
        self.base = base
        self.root = base / "repo"
        self.results = base / "results"
        hooks = base / "nohooks"
        for d in (self.root, self.results, hooks):
            d.mkdir()

        # A git hook environment could point every git call at another repo.
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for key in _GIT_ENV:
            os.environ.pop(key, None)

        self._git("init", "-q")
        for key, value in (("user.email", "t@t"), ("user.name", "t"),
                           ("commit.gpgsign", "false"), ("core.autocrlf", "false"),
                           ("core.hooksPath", str(hooks))):
            self._git("config", key, value)

        for name, value in (("REPO_ROOT", self.root),
                            ("PREREG", self.root / "eval" / "prereg")):
            p = mock.patch.object(prereg, name, value)
            p.start()
            self.addCleanup(p.stop)
        self.assertTrue(prereg.PREREG.resolve().is_relative_to(base))
        prereg.PREREG.mkdir(parents=True)

    def _git(self, *args, when=None):
        env = dict(os.environ)
        if when is not None:
            stamp = "@{} +0000".format(when)
            env.update(GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        return subprocess.run(["git"] + list(args), cwd=str(self.root), env=env,
                              check=True, capture_output=True, text=True)

    def _write(self, name, spec=None):
        path = prereg.PREREG / (name + ".json")
        path.write_text(json.dumps(spec or GATES, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
        return path

    def _commit(self, when, message="prereg"):
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message, when=when)

    def _register(self, name, when, spec=None):
        path = self._write(name, spec)
        self._commit(when)
        return path

    def _benchmark(self, when, data=None):
        b = self.results / "benchmark.json"
        b.write_text(json.dumps(data or {}), encoding="utf-8")
        os.utime(b, (when, when))
        return b

    def problems(self, name, bench):
        # Never let a failed patch send this at the real record.
        self.assertTrue(prereg.PREREG.resolve().is_relative_to(self.base))
        self.assertTrue(prereg.REPO_ROOT.resolve().is_relative_to(self.base))
        return prereg.registration_problems(name, bench)

    def test_committed_before_the_results_is_accepted(self):
        self._register("EARLY", T0)
        self.assertEqual([], self.problems("EARLY", self._benchmark(T0 + HOUR)))

    def test_committed_in_the_same_second_as_the_results_is_refused(self):
        self._register("TIE", T0)
        problems = self.problems("TIE", self._benchmark(T0))
        self.assertEqual(1, len(problems), problems)
        self.assertIn("not a threshold", problems[0])

    def test_committed_after_the_results_is_refused(self):
        self._register("LATE", T0 + HOUR)
        problems = self.problems("LATE", self._benchmark(T0))
        self.assertEqual(1, len(problems), problems)
        self.assertIn("not a threshold", problems[0])

    def test_edited_on_disk_after_the_results_is_refused(self):
        self._register("EDITED", T0)
        bench = self._benchmark(T0 + HOUR)
        self._write("EDITED", dict(GATES, primary_threshold_points=1.0))
        problems = self.problems("EDITED", bench)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("differs from HEAD", problems[0])

    def test_an_edit_staged_but_not_committed_is_refused(self):
        self._register("STAGED", T0)
        bench = self._benchmark(T0 + HOUR)
        self._write("STAGED", dict(GATES, primary_threshold_points=1.0))
        self._git("add", "-A")
        problems = self.problems("STAGED", bench)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("differs from HEAD", problems[0])

    def test_an_edit_committed_after_the_results_is_refused(self):
        """Registered in time, then quietly moved and committed again."""
        self._register("MOVED", T0)
        bench = self._benchmark(T0 + HOUR)
        self._register("MOVED", T0 + 2 * HOUR,
                       dict(GATES, primary_threshold_points=1.0))
        problems = self.problems("MOVED", bench)
        self.assertEqual(1, len(problems), problems)
        self.assertIn("not a threshold", problems[0])

    def test_a_later_commit_to_another_file_does_not_count(self):
        self._register("KEPT", T0)
        bench = self._benchmark(T0 + HOUR)
        (self.root / "notes.txt").write_text("later\n", encoding="utf-8")
        self._commit(T0 + 2 * HOUR, "unrelated")
        self.assertEqual([], self.problems("KEPT", bench))

    def test_an_untracked_registration_is_refused(self):
        self._write("UNTRACKED")
        problems = self.problems("UNTRACKED", self._benchmark(T0 + HOUR))
        self.assertEqual(1, len(problems), problems)
        self.assertIn("not tracked", problems[0])

    def test_a_deleted_registration_is_refused(self):
        path = self._register("GONE", T0)
        path.unlink()
        problems = self.problems("GONE", self._benchmark(T0 + HOUR))
        self.assertEqual(1, len(problems), problems)
        self.assertIn("does not exist", problems[0])

    def test_register_will_not_overwrite_a_registration(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, prereg.register("ONCE", 15.0, 2, 40.0, ""))
        with self.assertRaises(SystemExit) as caught:
            prereg.register("ONCE", 1.0, 2, 40.0, "")
        self.assertIn("already exists", str(caught.exception))
        spec = json.loads((prereg.PREREG / "ONCE.json").read_text(encoding="utf-8"))
        self.assertEqual(15.0, spec["primary_threshold_points"])

    def _verdict(self, name, bench):
        self.problems(name, bench)   # the safety asserts
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = prereg.verdict(name, bench)
        return code, out.getvalue() + err.getvalue()

    def test_verdict_scores_an_early_registration(self):
        self._register("V_EARLY", T0)
        code, text = self._verdict("V_EARLY", self._benchmark(T0 + HOUR, arms()))
        self.assertEqual(0, code, text)
        self.assertIn("VERDICT: PROVEN", text)

    def test_verdict_refuses_a_late_registration_of_the_same_numbers(self):
        self._register("V_LATE", T0 + 2 * HOUR)
        code, text = self._verdict("V_LATE", self._benchmark(T0 + HOUR, arms()))
        self.assertEqual(1, code, text)
        self.assertIn("not a threshold", text)
        self.assertNotIn("PROVEN", text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
