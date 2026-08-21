#!/usr/bin/env python3
"""to_benchmark.py -- score staged answers into skill-creator's benchmark.json.

    python eval/harness/to_benchmark.py --staging DIR --assign assign.json \\
        --out eval/runs/F004/benchmark.json

WHY AN ADAPTER RATHER THAN skill-creator's GRADER

skill-creator grades with a subagent because most skills produce prose. t004
has a deterministic key -- a fake Certis client that records what was
submitted -- so an LLM grader would add variance and cost for nothing. This
emits skill-creator's schema from that key, so `prereg.py --verdict` and
skill-creator's own viewer both read the result.

Field names are the documented ones and tests/test_prereg.py asserts they still
exist upstream.

WHICH CHECKS BECOME THE PRIMARY NUMBERS, AND WHY IT IS NOT ALL OF THEM

docs/design-F004.md pre-registered the +40 bar "on the absent checks", so the
`t004` eval this emits carries the ABSENT checks only.

That is not a convenience. Pooling all eight t004 checks would put the oracle
at 8/8 and the control at 5/8 -- a lift of +37.5, under the registered +40 --
while the absent checks themselves run 0% against 100%. The pooled number would
fail the task for a reason that has nothing to do with the task: it would be
measuring how many easy checks were bundled alongside the hard ones.

The functional and conventional checks are the sanity floor. They are graded,
written to `floor.json` next to the benchmark, and summarised on stdout. A
sample that fails them is reported loudly, because a control that cannot do the
job at all makes the run unreadable rather than informative.

A LESSON WORTH THE COMMENT

The registration was committed before the fixture existed, so it could not name
which checks the threshold applied to -- only the design doc did. That worked
out here because the doc is unambiguous and predates the run too, but it was
luck. Register after the key exists, and put the check kind in the file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import run_checks as rc  # noqa: E402

PRIMARY_KIND = "absent"
FLOOR_KINDS = ("functional", "conventional")


def _show(path: Path) -> str:
    """Display path, never a crash: --out may be anywhere."""
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def build(staging: Path, assign: dict, out: Path):
    tasks = rc.load_tasks()
    runs, floor_rows, per_config = [], [], {}

    for code, config in sorted(assign.items()):
        per_config.setdefault(config, 0)
        per_config[config] += 1
        run_number = per_config[config]

        for eval_id, task in enumerate(tasks, start=1):
            answer = (staging / code / "meridian" / task["package"]
                      / task["module"])
            result = rc.score(answer, task["task"],
                              package=task["package"], module=task["module"])
            key = rc.load_key(task["task"])
            kinds = {c["id"]: c["kind"] for c in key.CHECKS}
            is_harm = task["task"] != "t004"

            # The harm eval is graded whole -- the question there is whether
            # installing the skill moved anything, not which kind moved.
            wanted = (list(kinds) if is_harm
                      else [c for c, k in kinds.items() if k == PRIMARY_KIND])
            expectations = [
                {"text": cid, "passed": bool(result["checks"][cid]["ok"]),
                 "evidence": (result["checks"][cid]["error"] or "")[:300]}
                for cid in wanted]
            passed = sum(1 for e in expectations if e["passed"])
            total = len(expectations)
            runs.append({
                "eval_id": eval_id, "eval_name": task["task"],
                "configuration": config, "run_number": run_number,
                "result": {"pass_rate": (passed / total) if total else 0.0,
                           "passed": passed, "failed": total - passed,
                           "total": total, "time_seconds": 0.0, "tokens": 0,
                           "tool_calls": 0, "errors": 0},
                "expectations": expectations,
                "notes": ([result["import_error"]] if result["import_error"]
                          else []),
            })

            if not is_harm:
                floor = [{"check": cid, "kind": kinds[cid],
                          "passed": bool(result["checks"][cid]["ok"]),
                          "error": result["checks"][cid]["error"]}
                         for cid, k in kinds.items() if k in FLOOR_KINDS]
                floor_rows.append({"code": code, "configuration": config,
                                   "checks": floor})

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "metadata": {"skill_name": "certis-verification",
                     "runs_per_configuration": max(per_config.values())
                     if per_config else 0,
                     "primary_kind": PRIMARY_KIND},
        "runs": runs}, indent=2) + "\n", encoding="utf-8", newline="\n")

    floor_path = out.parent / "floor.json"
    floor_path.write_text(json.dumps(floor_rows, indent=2) + "\n",
                          encoding="utf-8", newline="\n")

    print("wrote {} ({} runs across {} configuration(s))".format(
        _show(out), len(runs), len(per_config)))
    print("wrote {}".format(_show(floor_path)))

    broken = [(r["code"], r["configuration"],
               [c["check"] for c in r["checks"] if not c["passed"]])
              for r in floor_rows]
    broken = [b for b in broken if b[2]]
    print("\nSANITY FLOOR")
    if broken:
        for code, config, failed in broken:
            print("  {} ({}) failed {}".format(code, config, ", ".join(failed)))
        print("\n  {} sample(s) could not do the job at all. Read those answers "
              "before\n  trusting any number above them -- a control that fails "
              "the floor makes\n  the run unreadable rather than "
              "informative.".format(len(broken)))
    else:
        print("  every sample passed every functional and conventional check.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--staging", required=True)
    ap.add_argument("--assign", required=True,
                    help="JSON mapping staged directory name -> configuration")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    assign = json.loads(Path(args.assign).read_text(encoding="utf-8"))
    return build(Path(args.staging).resolve(), assign,
                 Path(args.out).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
