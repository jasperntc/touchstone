#!/usr/bin/env python3
"""prereg.py -- the gates skill-creator does not have.

    python eval/harness/prereg.py --register F004 --threshold 15
    python eval/harness/prereg.py --verdict  F004 --benchmark <path>/benchmark.json
    python eval/harness/prereg.py --check-prompts base.txt treated.txt --treatment b.txt

WHY THIS IS SMALL, AND WHY IT SITS ON TOP OF SOMETHING ELSE

skill-creator (`anthropics/claude-plugins-official`) already runs the loop this
repository spent three fixtures rebuilding: with-skill and baseline subagents
spawned together, a grader, `aggregate_benchmark.py` with mean/stddev/delta, a
comparator that judges A against B without being told which is which, an
analyzer that flags expectations which "always pass in both configurations",
and description tuning with a 60/40 train/held-out split.

All of that is better than what was here, and `blind_run.py` was deleted rather
than maintained beside it. What follows is the remainder -- gates skill-creator
does not have, each of which has already produced a false reading in this
project or its predecessor.

    1. AN UPPER CONTROL. skill-creator's baseline is `without_skill` or the
       previous version of the skill. No arm hands the answer over outright, so
       a run cannot separate "the skill adds nothing" from "nothing could have
       added anything". agency-agents spent 44 blind subagents inside that
       ambiguity. Its analyzer does flag an expectation that always passes in
       both arms, but afterwards, as an observation -- not as a stop before the
       fleet is spent.

       Here `oracle` is required, and if it does not beat `without_skill` the
       TASK is rejected and the skill is never scored. No skill beats a ceiling.

    2. A THRESHOLD FIXED BEFORE THE RUN. skill-creator drafts assertions while
       the runs are in flight, which is right for authoring and wrong for
       deciding. F002 landed at +12.5 against a bar of +15, and the only reason
       that was a failure rather than "promising" is that the bar was in git
       first. `--verdict` refuses to score unless the registration is committed
       and its commit predates the run.

    3. ONE NUMBER IS NOT ONE FINDING. F002 and F003 both produced a pooled lift
       near +12 in which a single expectation carried the entire effect. A
       pooled average hides that completely, so `--verdict` also counts how many
       distinct expectations separate the arms and enforces a floor on it.

`--check-prompts` is the fourth and smallest: it asserts two arms' prompts
differ by the treatment and nothing else. Every other difference is an
uncontrolled variable, and they are easy to introduce by hand.

`evaluate()` is deliberately pure -- spec and parsed benchmark in, decision out,
no git and no filesystem -- because the gate deciding wrongly is the failure
that matters and it has to be testable without staging a real run.
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PREREG = REPO_ROOT / "eval" / "prereg"

REQUIRED_CONFIGS = ("without_skill", "oracle", "with_skill")


def _git(*args, cwd=None):
    # Resolved at call time, not bound as a default: the tests point REPO_ROOT
    # and PREREG at a throwaway repository, and a default argument would have
    # captured the real one at import and quietly tested nothing.
    return subprocess.run(["git"] + list(args), cwd=str(cwd or REPO_ROOT),
                          capture_output=True, text=True, check=False)


def register(name, threshold, min_discriminating, min_gap, note,
             min_captured=0.0, harm_eval="", harm_tolerance=5.0) -> int:
    PREREG.mkdir(parents=True, exist_ok=True)
    path = PREREG / (name + ".json")
    if path.exists():
        raise SystemExit(
            "{} already exists. A threshold that can be rewritten after the "
            "run is not a threshold; start a new run id instead.".format(
                path.relative_to(REPO_ROOT).as_posix()))
    path.write_text(json.dumps({
        "run": name,
        "primary_threshold_points": threshold,
        "min_discriminating_expectations": min_discriminating,
        "discriminating_gap_points": min_gap,
        "required_configurations": list(REQUIRED_CONFIGS),
        "min_captured_percent": min_captured,
        "harm_eval": harm_eval,
        "harm_tolerance_points": harm_tolerance,
        "note": note,
    }, indent=2) + "\n", encoding="utf-8", newline="\n")
    rel = path.relative_to(REPO_ROOT).as_posix()
    print("wrote " + rel)
    print()
    print("COMMIT THIS BEFORE YOU SPAWN ANYTHING. --verdict reads the commit")
    print("timestamp and refuses to score a run that started first.")
    print()
    print("    git add {} && git commit -m 'prereg: {}'".format(rel, name))
    return 0


def _pooled(runs):
    """Pooled pass rate over every expectation in every run of a config.

    Pooled rather than a mean of per-run rates: a short run should not weigh as
    much as a long one. The mean and stddev are carried alongside because those
    are the numbers skill-creator's own benchmark shows.
    """
    passed = sum(r["result"].get("passed", 0) for r in runs)
    total = sum(r["result"].get("total", 0) for r in runs)
    rates = [100.0 * r["result"].get("pass_rate", 0.0) for r in runs]
    return {
        "pooled": 100.0 * passed / total if total else 0.0,
        "mean": statistics.fmean(rates) if rates else 0.0,
        "stddev": statistics.stdev(rates) if len(rates) > 1 else 0.0,
        "runs": len(runs), "passed": passed, "total": total,
    }


def _by_expectation(runs_by_config):
    """Pass rate per (eval, expectation) per configuration."""
    table = {}
    for config, runs in runs_by_config.items():
        for run in runs:
            for exp in run.get("expectations", []):
                key = (str(run.get("eval_name") or run.get("eval_id")), exp["text"])
                cell = table.setdefault(key, {}).setdefault(
                    config, {"passed": 0, "total": 0})
                cell["total"] += 1
                cell["passed"] += 1 if exp.get("passed") else 0
    return table


def evaluate(spec, data):
    """Decide, from a registration and a parsed benchmark. No IO."""
    runs_by_config = {}
    for run in data.get("runs", []):
        runs_by_config.setdefault(run["configuration"], []).append(run)

    missing = [c for c in spec["required_configurations"]
               if c not in runs_by_config]
    if missing:
        return {"ok": False, "verdict": "UNREADABLE", "missing": missing}

    # A skill is installed into a whole project, not just onto the task it was
    # written for. `harm_eval` names a task the skill has no business
    # improving; its runs are held out of the primary numbers entirely and
    # checked separately for regression. Pooling them in would let a skill that
    # damages unrelated work hide inside a good average, and "does installing
    # this make anything worse" is the question a COLLECTION has to answer that
    # a single skill's own eval never asks.
    harm_name = spec.get("harm_eval") or ""
    harm_runs, main_runs = {}, {}
    for config, rs in runs_by_config.items():
        main_runs[config] = [r for r in rs
                             if str(r.get("eval_name")) != harm_name]
        drop = [r for r in rs if str(r.get("eval_name")) == harm_name]
        if drop:
            harm_runs[config] = drop
    if not any(main_runs.values()):
        return {"ok": False, "verdict": "UNREADABLE",
                "missing": ["every eval is the harm eval"]}
    runs_by_config = main_runs

    stats = {c: _pooled(r) for c, r in runs_by_config.items()}
    base = stats["without_skill"]["pooled"]
    headroom = stats["oracle"]["pooled"] - base
    lift = stats["with_skill"]["pooled"] - base

    table = _by_expectation(runs_by_config)
    rows, discriminating = [], []
    for key, cells in sorted(table.items()):
        def rate(cfg):
            c = cells.get(cfg)
            return 100.0 * c["passed"] / c["total"] if c and c["total"] else 0.0
        gap = rate("with_skill") - rate("without_skill")
        rows.append((key, rate("without_skill"), rate("with_skill"), gap))
        if gap >= spec["discriminating_gap_points"]:
            discriminating.append(key)

    if headroom <= 0:
        return {"ok": False, "verdict": "TASK REJECTED", "missing": [],
                "stats": stats, "headroom": headroom, "lift": lift,
                "rows": rows, "discriminating": discriminating,
                "captured": 0.0, "ceiling_ok": False,
                "lift_ok": False, "spread_ok": False}

    lift_ok = lift >= spec["primary_threshold_points"]
    spread_ok = len(discriminating) >= spec["min_discriminating_expectations"]
    captured = 100.0 * lift / headroom if headroom > 0 else 0.0

    # When the information is genuinely absent from the codebase, the oracle
    # beats the control BY CONSTRUCTION, and an absolute lift then proves
    # nothing about the skill -- only that the facts help, which was never in
    # doubt. What is worth measuring is how much of the headroom the oracle
    # proved exists the PACKAGED skill actually delivers.
    min_captured = spec.get("min_captured_percent") or 0.0
    captured_ok = captured >= min_captured

    harm_stats, harm_delta, harm_ok = None, None, True
    if harm_runs.get("with_skill") and harm_runs.get("without_skill"):
        harm_stats = {c: _pooled(r) for c, r in harm_runs.items()}
        harm_delta = (harm_stats["with_skill"]["pooled"]
                      - harm_stats["without_skill"]["pooled"])
        harm_ok = harm_delta >= -abs(spec.get("harm_tolerance_points", 5.0))
    elif harm_name:
        harm_ok = False   # declared but produced no runs: an untested claim

    ok = lift_ok and spread_ok and captured_ok and harm_ok
    return {
        "ok": ok,
        "verdict": "PROVEN" if ok else "NOT PROVEN",
        "missing": [], "stats": stats, "headroom": headroom, "lift": lift,
        "rows": rows, "discriminating": discriminating, "captured": captured,
        "ceiling_ok": True, "lift_ok": lift_ok, "spread_ok": spread_ok,
        "captured_ok": captured_ok, "min_captured": min_captured,
        "harm_stats": harm_stats, "harm_delta": harm_delta, "harm_ok": harm_ok,
        "harm_eval": harm_name,
    }


def registration_problems(name, benchmark: Path):
    """The threshold must be in git, unmodified, and older than the run."""
    path = PREREG / (name + ".json")
    rel = path.relative_to(REPO_ROOT).as_posix()
    if not path.exists():
        return ["{} does not exist -- nothing was registered".format(rel)]
    problems = []
    if _git("ls-files", "--error-unmatch", rel).returncode != 0:
        return ["{} is not tracked by git, so nothing fixes it in time".format(rel)]
    if _git("diff", "--quiet", "HEAD", "--", rel).returncode != 0:
        problems.append("{} differs from HEAD -- the committed threshold is not "
                        "the one on disk".format(rel))
    stamp = _git("log", "-1", "--format=%ct", "--", rel).stdout.strip()
    if not stamp:
        return problems + ["{} has no commit -- it was never committed".format(rel)]
    if int(stamp) >= int(benchmark.stat().st_mtime):
        problems.append(
            "{} was committed at or after the benchmark was written. A "
            "threshold set after the numbers is not a threshold.".format(rel))
    return problems


def verdict(name, benchmark: Path) -> int:
    problems = registration_problems(name, benchmark)
    if problems:
        for p in problems:
            print("FAILED: " + p, file=sys.stderr)
        return 1

    spec = json.loads((PREREG / (name + ".json")).read_text(encoding="utf-8"))
    out = evaluate(spec, json.loads(benchmark.read_text(encoding="utf-8")))

    if out["verdict"] == "UNREADABLE":
        print("FAILED: no {} arm in this benchmark.".format(
            ", ".join(out["missing"])), file=sys.stderr)
        if "oracle" in out["missing"]:
            print("        Without an upper control a null is unreadable -- it "
                  "cannot tell\n        'the skill adds nothing' from 'nothing "
                  "could have added anything'.", file=sys.stderr)
        return 1

    print("ARMS")
    for config in spec["required_configurations"]:
        s = out["stats"][config]
        print("  {:<14} {:>5.1f}% pooled ({}/{})   {:>5.1f}% +/- {:.1f} over "
              "{} run(s)".format(config, s["pooled"], s["passed"], s["total"],
                                 s["mean"], s["stddev"], s["runs"]))

    print("\nPER EXPECTATION")
    print("  {:<46} {:>6} {:>6} {:>7}".format("expectation", "none", "skill", "gap"))
    for (eval_name, text), none_rate, skill_rate, gap in out["rows"]:
        label = "{}: {}".format(eval_name, text)
        print("  {:<46} {:>5.0f}% {:>5.0f}% {:>+7.0f}".format(
            label[:46], none_rate, skill_rate, gap))

    print("\nGATES, from {}".format(
        (PREREG / (name + ".json")).relative_to(REPO_ROOT).as_posix()))
    print("  headroom     oracle - without_skill = {:+.1f}   {}".format(
        out["headroom"], "ok" if out["ceiling_ok"] else "TASK REJECTED"))
    if not out["ceiling_ok"]:
        print("               The task is at a ceiling. No skill can beat it, so")
        print("               the skill is not scored -- fix the task.")
        print("\n  VERDICT: TASK REJECTED")
        return 1
    print("  lift         with_skill - without_skill = {:+.1f} vs {:+.1f}   {}"
          .format(out["lift"], spec["primary_threshold_points"],
                  "MET" if out["lift_ok"] else "MISSED"))
    print("  spread       {} expectation(s) with a gap >= {:.0f} vs {}   {}".format(
        len(out["discriminating"]), spec["discriminating_gap_points"],
        spec["min_discriminating_expectations"],
        "MET" if out["spread_ok"] else "MISSED"))
    print("  captured     {:.0f}% of the headroom the oracle proved is there{}"
          .format(out["captured"],
                  "   vs {:.0f}%   {}".format(
                      out["min_captured"],
                      "MET" if out["captured_ok"] else "MISSED")
                  if out["min_captured"] else ""))
    if out["harm_eval"]:
        if out["harm_delta"] is None:
            print("  no harm      {} declared but produced no runs   MISSED"
                  .format(out["harm_eval"]))
        else:
            print("  no harm      {} moved {:+.1f}, tolerance -{:.0f}   {}".format(
                out["harm_eval"], out["harm_delta"],
                abs(spec.get("harm_tolerance_points", 5.0)),
                "ok" if out["harm_ok"] else "REGRESSED"))
    print("\n  VERDICT: {}".format(out["verdict"]))
    if not out["ok"]:
        print("           Nothing enters skills/ on this run.")
    return 0 if out["ok"] else 1


def check_prompts(baseline: Path, treated: Path, treatment: Path) -> int:
    """The arms must differ by the treatment and by nothing else."""
    a = baseline.read_text(encoding="utf-8")
    b = treated.read_text(encoding="utf-8")
    block = treatment.read_text(encoding="utf-8")
    if block not in b:
        print("FAILED: the treatment block does not appear in {}".format(
            treated.name), file=sys.stderr)
        return 1
    stripped = b.replace(block, "", 1)
    if stripped != a:
        import difflib
        print("FAILED: with the treatment removed the two arms still differ. "
              "Every\n        remaining difference is an uncontrolled variable.",
              file=sys.stderr)
        for line in list(difflib.unified_diff(
                a.splitlines(), stripped.splitlines(), baseline.name,
                treated.name + " minus treatment", lineterm=""))[:20]:
            print("  " + line, file=sys.stderr)
        return 1
    print("PASSED: the arms differ by the treatment and nothing else.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--register", metavar="RUN")
    ap.add_argument("--verdict", metavar="RUN")
    ap.add_argument("--benchmark", metavar="PATH")
    ap.add_argument("--threshold", type=float, default=15.0)
    ap.add_argument("--min-discriminating", type=int, default=2)
    ap.add_argument("--gap", type=float, default=40.0)
    ap.add_argument("--note", default="")
    ap.add_argument("--min-captured", type=float, default=0.0,
                    help="percent of the oracle's headroom the skill must deliver")
    ap.add_argument("--harm-eval", default="",
                    help="an eval the skill should NOT change; held out of the "
                         "primary numbers and checked for regression")
    ap.add_argument("--harm-tolerance", type=float, default=5.0)
    ap.add_argument("--check-prompts", nargs=2, metavar=("BASE", "TREATED"))
    ap.add_argument("--treatment", metavar="PATH")
    args = ap.parse_args()

    if args.register:
        return register(args.register, args.threshold, args.min_discriminating,
                        args.gap, args.note, args.min_captured,
                        args.harm_eval, args.harm_tolerance)
    if args.check_prompts:
        if not args.treatment:
            raise SystemExit("--check-prompts needs --treatment")
        return check_prompts(Path(args.check_prompts[0]),
                             Path(args.check_prompts[1]), Path(args.treatment))
    if args.verdict:
        if not args.benchmark:
            raise SystemExit("--verdict needs --benchmark")
        return verdict(args.verdict, Path(args.benchmark))
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
