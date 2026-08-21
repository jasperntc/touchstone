#!/usr/bin/env python3
"""run_checks.py -- score one answer against one task's key.

    python eval/harness/run_checks.py --self-test
    python eval/harness/run_checks.py --calibrate
    python eval/harness/run_checks.py --answer <path> --task t001

WHAT THIS INHERITS, AND WHY

Ported from agency-agents, which spent a week discovering that its instruments
mattered more than its corpus. The parts kept are the ones that caught real
errors there:

  two-sided calibration   a reference must pass every check, and a naive draft
                          must clear the functional floor while FAILING at
                          least one conventional check per task. A task where
                          the naive draft scores well cannot separate anything,
                          and that is a defect in the task, not the answer.

  kinds never blended     `functional` and `conventional` are reported apart,
                          always. The moment they are averaged, a good score on
                          the easy half hides a null on the discriminating half.

  the key is withheld     eval/tasks/key/ holds the answer. It is moved out of
                          the working tree while answers are collected, exactly
                          as the suites were there. tasks.jsonl carries the
                          QUESTION only, because a `why` field in the question
                          file turned out to be the answer in one sentence.

WHAT IS NEW HERE, AND WHY IT IS THE POINT

An ORACLE condition. agency-agents had two lower controls -- `none` and a
body-stripped `flattened` -- and no upper one, so when construction scored
24/24 in every cell there was no way to tell "the skill adds nothing" from
"nothing could have added anything". Three task designs and 44 blind subagents
went into that ceiling before it was diagnosed.

    none      the task, the codebase, no conventions.        LOWER control.
    oracle    the task, the codebase, CONVENTIONS.md.        UPPER control.
    <skill>   the task, the codebase, the skill under test.

If `oracle` does not beat `none`, the TASK IS REJECTED before any skill is
written. That single rule is the lesson of the previous project, expressed as
code: calibrate the instrument before trusting a null from it.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "eval" / "fixture"
KEYS = REPO_ROOT / "eval" / "tasks" / "key"
TASKS = REPO_ROOT / "eval" / "tasks" / "tasks.jsonl"

CONDITIONS = {
    "none": "The task and the codebase. No conventions supplied. LOWER control.",
    "oracle": "The task, the codebase, and CONVENTIONS.md handed over verbatim. "
              "UPPER control -- proves the task is winnable with the right "
              "information, which is the thing a null cannot tell you.",
    "skill": "The task, the codebase, and the skill under test.",
}


def load_tasks() -> list[dict]:
    if not TASKS.exists():
        return []
    return [json.loads(line) for line in TASKS.read_text(encoding="utf-8").splitlines()
            if line.strip()]


def load_key(task_id: str):
    path = KEYS / f"{task_id}.py"
    if not path.exists():
        raise SystemExit(
            f"{path.relative_to(REPO_ROOT).as_posix()} is missing. The key is "
            f"moved out of the tree while answers are collected; restore it "
            f"before scoring.")
    spec = importlib.util.spec_from_file_location(f"key_{task_id}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def score(answer: Path, task_id: str, *, package: str = "",
          module: str = "balance.py") -> dict:
    """Run one answer against one key, in a scratch copy of the fixture.

    A subprocess and a throwaway tree, so a module that mutates fixture state
    cannot leak into the next answer's score.
    """
    key = load_key(task_id)
    kinds = {c["id"]: c["kind"] for c in key.CHECKS}

    def every(reason: str) -> dict:
        return {"import_error": reason,
                "checks": {cid: {"ok": False, "error": reason, "kind": k}
                           for cid, k in kinds.items()}}

    if not answer.exists():
        return every("answer was never written")

    with tempfile.TemporaryDirectory(prefix="touchstone-") as scratch:
        tree = Path(scratch)
        shutil.copytree(FIXTURE / "meridian", tree / "meridian")
        dest = tree / "meridian"
        if package:
            dest = dest / package
            dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(answer, dest / module)
        runner = tree / "_run.py"
        import_path = ("meridian." + package + "." + module[:-3]
                       if package else "meridian." + module[:-3])
        runner.write_text(RUNNER_SRC, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-I", str(runner), str(KEYS / f"{task_id}.py"),
             import_path],
            capture_output=True, text=True, cwd=scratch, timeout=60, check=False)

    try:
        raw = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return every(f"runner produced no result: {tail[-1] if tail else '?'}")

    for cid, entry in raw["checks"].items():
        entry["kind"] = kinds.get(cid, "?")
    return raw


RUNNER_SRC = '''
import importlib.util, json, sys, traceback
from pathlib import Path

key_path = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("key", key_path)
key = importlib.util.module_from_spec(spec); spec.loader.exec_module(key)

sys.path.insert(0, ".")
out = {"import_error": None, "checks": {}}
try:
    import importlib
    answer = importlib.import_module(sys.argv[2])
    src = Path(answer.__file__).read_text(encoding="utf-8")
except Exception as exc:
    out["import_error"] = f"{type(exc).__name__}: {exc}"
    for c in key.CHECKS:
        out["checks"][c["id"]] = {"ok": False, "error": out["import_error"]}
    print(json.dumps(out)); raise SystemExit(0)

for c in key.CHECKS:
    fn = getattr(key, "check_" + c["id"], None)
    if fn is None:
        out["checks"][c["id"]] = {"ok": False, "error": "no check function"}
        continue
    try:
        fn(answer, src)
        out["checks"][c["id"]] = {"ok": True, "error": None}
    except AssertionError as exc:
        out["checks"][c["id"]] = {"ok": False, "error": str(exc) or "AssertionError"}
    except Exception as exc:
        out["checks"][c["id"]] = {"ok": False,
                                  "error": f"{type(exc).__name__}: {exc}"}
print(json.dumps(out))
'''


def by_kind(result: dict) -> dict:
    out: dict = {}
    for cid, entry in result["checks"].items():
        bucket = out.setdefault(entry["kind"], {"passed": 0, "total": 0, "failed": []})
        bucket["total"] += 1
        if entry["ok"]:
            bucket["passed"] += 1
        else:
            bucket["failed"].append(cid)
    return out


def run_set(directory: Path) -> dict:
    out = {}
    for task in load_tasks():
        out[task["task"]] = score(directory / task["module"], task["task"],
                                  package=task.get("package", ""),
                                  module=task["module"])
    return out


def self_test() -> int:
    """A competent implementation must pass every check."""
    broken = 0
    for tid, result in run_set(REPO_ROOT / "eval" / "reference").items():
        kinds = by_kind(result)
        failed = [c for k in kinds.values() for c in k["failed"]]
        total = sum(k["total"] for k in kinds.values())
        passed = sum(k["passed"] for k in kinds.values())
        print(f"  {tid}  {passed}/{total}  {'ok' if not failed else 'BROKEN'}")
        for cid in failed:
            print(f"      {cid}: {result['checks'][cid]['error']}")
        broken += len(failed)
    if broken:
        print(f"\nFAILED: {broken} check(s) reject a correct implementation. "
              f"Fix the check, not the answer.", file=sys.stderr)
        return 1
    print("\nPASSED: every check is satisfiable by someone who knows the "
          "conventions.")
    return 0


def calibrate() -> int:
    """The naive draft must clear the floor and fail the discriminator."""
    floor_broken, cannot_separate = [], []
    for tid, result in run_set(REPO_ROOT / "eval" / "naive").items():
        kinds = by_kind(result)
        func = kinds.get("functional", {"passed": 0, "total": 0, "failed": []})
        conv = kinds.get("conventional", {"passed": 0, "total": 0, "failed": []})
        print(f"  {tid}  functional {func['passed']}/{func['total']}   "
              f"conventional {conv['passed']}/{conv['total']}")
        for cid in conv["failed"]:
            print(f"      caught: {cid}")
        if func["failed"]:
            floor_broken.append((tid, func["failed"]))
        if not conv["failed"]:
            cannot_separate.append(tid)

    if floor_broken:
        for tid, failed in floor_broken:
            print(f"\nFAILED: {tid} rejects the naive draft on a FUNCTIONAL "
                  f"check ({', '.join(failed)}). The floor has to be reachable "
                  f"without knowing the conventions, or the conventional rate "
                  f"is unreadable.", file=sys.stderr)
        return 1
    if cannot_separate:
        print(f"\nFAILED: {', '.join(cannot_separate)} pass every conventional "
              f"check without being told the conventions. Those tasks cannot "
              f"separate anything and must not be used.", file=sys.stderr)
        return 1
    print("\nPASSED: the floor is reachable and every task can discriminate.")
    return 0


def drafts() -> int:
    """Score all three calibration drafts and require the middle one to be exact.

    --self-test proves the ceiling is reachable and --calibrate proves the
    floor is not the ceiling. Neither notices the failure that actually
    threatens this fixture: a narrow convention quietly becoming visible in
    the package the task lives in, which would leave every gate green while
    silently turning the experiment into a different one.

    So the partial draft -- a model that read accounts/ and nothing else --
    must fail EXACTLY the narrow set. Not a subset, not a superset.
    """
    rows, problems = [], []
    for name in ("reference", "partial", "naive"):
        for tid, result in run_set(REPO_ROOT / "eval" / name).items():
            kinds = by_kind(result)
            func = kinds.get("functional", {"passed": 0, "total": 0, "failed": []})
            conv = kinds.get("conventional", {"passed": 0, "total": 0, "failed": []})
            rows.append((name, tid, func, conv))
            print(f"  {name:<10} {tid}  functional {func['passed']}/{func['total']}"
                  f"   conventional {conv['passed']}/{conv['total']}")
            if func["failed"]:
                problems.append(f"{name}/{tid} fails a functional check "
                                f"({', '.join(func['failed'])}); the floor must be "
                                f"reachable without knowing the conventions")
            if name == "reference" and conv["failed"]:
                problems.append(f"reference/{tid} fails {conv['failed']}")
            if name == "naive" and conv["passed"]:
                problems.append(f"naive/{tid} passes {conv['passed']} conventional "
                                f"check(s) without being told anything")
            if name == "partial":
                expected = set(load_key(tid).NARROW)
                got = set(conv["failed"])
                if got != expected:
                    problems.append(
                        f"partial/{tid} fails {sorted(got)}; the narrow set is "
                        f"{sorted(expected)}. Extra means a wide convention is "
                        f"not actually wide; missing means a narrow one is "
                        f"reachable from inside the task's own package.")
    if problems:
        print()
        for p in problems:
            print(f"FAILED: {p}", file=sys.stderr)
        return 1
    print("\nPASSED: the instrument reads at three levels and the "
          "partial draft fails exactly the narrow set.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--drafts", action="store_true")
    ap.add_argument("--answer", metavar="PATH")
    ap.add_argument("--task", metavar="ID", default="t001")
    ap.add_argument("--conditions", action="store_true")
    args = ap.parse_args()

    if args.conditions:
        for name, why in CONDITIONS.items():
            print(f"{name:<8} {why}\n")
        return 0
    if args.self_test:
        return self_test()
    if args.calibrate:
        return calibrate()
    if args.drafts:
        return drafts()
    if args.answer:
        result = score(Path(args.answer), args.task)
        print(json.dumps({"task": args.task, "by_kind": by_kind(result),
                          "import_error": result["import_error"]}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
