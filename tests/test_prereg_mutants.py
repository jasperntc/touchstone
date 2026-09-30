"""Proof that test_prereg_gates.py can fail.

For each gate, one comparison in prereg.py is inverted in a temp copy, and
test_prereg_gates.py is run against that copy in a subprocess. A mutant counts
as caught only when a test FAILS or ERRORS. An expected failure that
unexpectedly passes does not count.

The real prereg.py is only ever read, and its hash is checked afterwards. The
copy lives at <tmp>/eval/harness/prereg.py, so the mutant's own REPO_ROOT and
PREREG point into the temp dir, not at the record.

    python -B tests/test_prereg_mutants.py     # prints mutant -> failing tests
"""
from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
PREREG_PY = REPO_ROOT / "eval" / "harness" / "prereg.py"
SUITE = "tests.test_prereg_gates"

# (gate, original, inverted). Each original must occur exactly once.
MUTANTS = [
    ("oracle", "if headroom <= 0:", "if headroom > 0:"),
    ("threshold", 'lift_ok = lift >= spec["primary_threshold_points"]',
     'lift_ok = lift < spec["primary_threshold_points"]'),
    ("spread count", "spread_ok = len(discriminating) >= spec",
     "spread_ok = len(discriminating) < spec"),
    ("spread gap", 'if gap >= spec["discriminating_gap_points"]:',
     'if gap < spec["discriminating_gap_points"]:'),
    ("capture", "captured_ok = captured >= min_captured",
     "captured_ok = captured < min_captured"),
    ("harm", "harm_ok = harm_delta >= -abs(", "harm_ok = harm_delta < -abs("),
    ("timing", "if int(stamp) >= int(benchmark.stat().st_mtime):",
     "if int(stamp) < int(benchmark.stat().st_mtime):"),
    ("edited", '_git("diff", "--quiet", "HEAD", "--", rel).returncode != 0',
     '_git("diff", "--quiet", "HEAD", "--", rel).returncode == 0'),
    ("tracked", '_git("ls-files", "--error-unmatch", rel).returncode != 0',
     '_git("ls-files", "--error-unmatch", rel).returncode == 0'),
]

# Runs in the subprocess: load the copy as `prereg` before the suite imports
# it, so every `import prereg` in the suite gets the copy.
RUNNER = r"""
import importlib.util, json, sys, unittest
sys.dont_write_bytecode = True
root, copy, suite = sys.argv[1:4]
sys.path.insert(0, root)
spec = importlib.util.spec_from_file_location("prereg", copy)
mod = importlib.util.module_from_spec(spec)
sys.modules["prereg"] = mod
spec.loader.exec_module(mod)
tests = unittest.defaultTestLoader.loadTestsFromName(suite)
res = unittest.TextTestRunner(stream=sys.stderr, verbosity=0).run(tests)
print("MUTANT-RESULT " + json.dumps({
    "prereg": mod.__file__, "run": res.testsRun,
    "failures": [t.id() for t, _ in res.failures],
    "errors": [t.id() for t, _ in res.errors],
    "unexpected_successes": [t.id() for t in res.unexpectedSuccesses],
}))
"""


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_suite(source: str):
    """Run SUITE against `source` as prereg.py. Returns the parsed result."""
    with tempfile.TemporaryDirectory(prefix="touchstone-mutant-") as tmp:
        copy = Path(tmp).resolve() / "eval" / "harness" / "prereg.py"
        copy.parent.mkdir(parents=True)
        copy.write_text(source, encoding="utf-8", newline="")
        proc = subprocess.run(
            [sys.executable, "-B", "-c", RUNNER, str(REPO_ROOT), str(copy), SUITE],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=600)
        lines = [ln for ln in proc.stdout.splitlines()
                 if ln.startswith("MUTANT-RESULT ")]
        if not lines:
            raise AssertionError("no result from the suite:\n" + proc.stderr[-3000:])
        result = json.loads(lines[-1][len("MUTANT-RESULT "):])
        if Path(result["prereg"]).resolve() != copy:
            raise AssertionError("the suite ran against {}, not the copy".format(
                result["prereg"]))
        result["killed_by"] = result["failures"] + result["errors"]
        return result


def mutate(source: str, original: str, inverted: str) -> str:
    count = source.count(original)
    if count != 1:
        raise AssertionError("{!r} occurs {} times in prereg.py".format(original, count))
    return source.replace(original, inverted)


class Mutants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = _sha(PREREG_PY)
        cls.source = PREREG_PY.read_bytes().decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        if _sha(PREREG_PY) != cls.before:
            raise AssertionError("eval/harness/prereg.py changed")

    def test_the_unmutated_copy_passes(self):
        result = run_suite(self.source)
        self.assertEqual([], result["killed_by"])
        self.assertEqual([], result["unexpected_successes"])
        self.assertGreater(result["run"], 0)

    def test_every_inverted_gate_fails_a_test(self):
        for gate, original, inverted in MUTANTS:
            with self.subTest(gate=gate):
                result = run_suite(mutate(self.source, original, inverted))
                self.assertTrue(result["killed_by"],
                                "inverting the {} gate failed no test".format(gate))


def main():
    before = _sha(PREREG_PY)
    source = PREREG_PY.read_bytes().decode("utf-8")
    rows = [("(none)", "", run_suite(source))]
    for gate, original, inverted in MUTANTS:
        rows.append((gate, "{}  ->  {}".format(original, inverted),
                     run_suite(mutate(source, original, inverted))))
    assert _sha(PREREG_PY) == before, "eval/harness/prereg.py changed"

    missed = 0
    for gate, change, r in rows:
        status = "caught" if r["killed_by"] else "passed"
        if gate != "(none)" and not r["killed_by"]:
            missed += 1
        print("{:<13} {:>2} failed / {} run   {}".format(
            gate, len(r["killed_by"]), r["run"], status))
        if change:
            print("    " + change)
        for t in r["killed_by"]:
            print("      " + t.replace(SUITE + ".", ""))
    print("\nprereg.py sha256 {} (unchanged)".format(before))
    return 1 if missed or rows[0][2]["killed_by"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
