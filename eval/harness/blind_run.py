#!/usr/bin/env python3
"""blind_run.py -- prepare a blind run, then score it.

    python eval/harness/blind_run.py --prepare F003 --samples 5
    python eval/harness/blind_run.py --collect F003

WHAT --prepare DOES

One staged copy of the fixture per sample, each in its own directory outside
every git repository, each verified by stage.verify() before its prompt is
written. Per-sample copies rather than one shared tree because F001's third
defect was samples writing into a visible shared directory: one subagent's grep
surfaced a sibling's answer and another watched two more appear mid-run.

Sample codes are opaque and carry no condition. The manifest that maps them
lives in the repository, never in the staging area, so a curious answerer
listing its own parent directory learns nothing.

The oracle prompt receives the conventions as TEXT. CONVENTIONS.md is never
written to disk in any condition -- see stage.py for why that matters -- and
the file's own framing (which run it belongs to, what an oracle is, what F001
got wrong) is stripped, because an answerer told it is the upper arm of an
experiment is not answering the same question as one told it has a style guide.

WHAT --collect DOES

Scores every answer against a PRISTINE copy of the fixture, not against the
tree the answer was written in, so an answer that edited a sibling module
cannot grade itself. Reports functional and conventional apart, per condition
and per check, and computes both thresholds from docs/prediction-F003.md
without knowing which way they came out.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import run_checks as rc          # noqa: E402
import stage as staging          # noqa: E402

STAGING = REPO_ROOT.parent / "_touchstone_staging"
RUNS = REPO_ROOT / "eval" / "runs"

# Fixed so a run is reproducible. Nothing in a code says which arm it is in.
CODES = {
    "none":   ["k7r", "m2v", "t9d", "b4x", "w6h", "j3p", "f8c", "n5g"],
    "oracle": ["p3n", "z8q", "c5j", "r1f", "y7s", "d6m", "v2k", "h9b"],
}

PROMPT = """You are implementing one function in an internal Python codebase \
called Meridian.

The codebase is here, and this is the only copy of it you should use:

    {path}

Work only inside that directory. Do not go looking for this project, or
anything related to it, anywhere else on this machine.

TASK

{brief}

Write your implementation to:

    {answer_path}

Create the file if it does not exist. Do not modify any other file.
{conventions}
WHEN YOU ARE DONE

Reply with exactly two sections and nothing else.

SOURCES
One line per file you opened and per command you ran to find information. If
any information you used came from somewhere other than reading files under
{path} -- a version control history, the internet, another directory on this
machine, or your own recollection of a similar codebase -- say so here
explicitly and name it.

NOTES
Anything you were unsure about or had to guess at, in two or three sentences.
"""

CONVENTIONS_BLOCK = """
HOUSE CONVENTIONS

Meridian has ten house conventions. They are this codebase's own choices rather
than industry standards, and current code follows all of them.

{rules}
"""


def conventions_text() -> str:
    """The numbered rules only, with this repository's own framing removed."""
    raw = (REPO_ROOT / "eval" / "fixture" / "CONVENTIONS.md").read_text(encoding="utf-8")
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("1. "):
            return "\n".join(lines[i:]).strip()
    raise SystemExit("CONVENTIONS.md has no numbered rules")


def prepare(run_id: str, samples: int) -> int:
    task = rc.load_tasks()[0]
    rules = conventions_text()
    leaked = [w for w in ("oracle", "F001", "F002", "F003", "condition", "control")
              if w.lower() in rules.lower()]
    if leaked:
        raise SystemExit(
            "the conventions text still carries this repository's framing "
            "({}); an answerer told it is an arm of an experiment is not "
            "answering the same question".format(", ".join(leaked)))

    out_dir = RUNS / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompts").mkdir(exist_ok=True)

    manifest = []
    for condition in ("none", "oracle"):
        for code in CODES[condition][:samples]:
            tree = staging.stage(STAGING / code)
            answer = tree / "meridian" / task["package"] / task["module"]
            prompt = PROMPT.format(
                path=tree.as_posix(),
                brief=task["brief"],
                answer_path=answer.as_posix(),
                conventions=CONVENTIONS_BLOCK.format(rules=rules)
                if condition == "oracle" else "")
            (out_dir / "prompts" / (code + ".txt")).write_text(
                prompt, encoding="utf-8", newline="\n")
            manifest.append({"code": code, "condition": condition,
                             "task": task["task"], "tree": tree.as_posix(),
                             "answer": answer.as_posix()})

    (out_dir / "manifest.json").write_text(
        json.dumps({"run": run_id, "samples": samples, "cells": manifest},
                   indent=2) + "\n", encoding="utf-8", newline="\n")

    # The two prompts must differ ONLY by the conventions block.
    a = (out_dir / "prompts" / (CODES["none"][0] + ".txt")).read_text(encoding="utf-8")
    b = (out_dir / "prompts" / (CODES["oracle"][0] + ".txt")).read_text(encoding="utf-8")
    a_stripped = a.replace(CODES["none"][0], "CODE")
    b_stripped = b.replace(CODES["oracle"][0], "CODE").replace(
        CONVENTIONS_BLOCK.format(rules=rules), "")
    if a_stripped != b_stripped:
        raise SystemExit(
            "the two arms differ by more than the conventions block; every "
            "other difference is an uncontrolled variable")

    print("staged {} trees under {}".format(len(manifest), STAGING))
    print("prompts in {}".format((out_dir / "prompts").relative_to(REPO_ROOT).as_posix()))
    print("the arms differ only by the conventions block: ok")
    return 0


def collect(run_id: str) -> int:
    out_dir = RUNS / run_id
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    task = rc.load_tasks()[0]
    key = rc.load_key(task["task"])
    order = [c["id"] for c in key.CHECKS]
    kinds = {c["id"]: c["kind"] for c in key.CHECKS}

    results = {}
    for cell in manifest["cells"]:
        result = rc.score(Path(cell["answer"]), cell["task"],
                          package=task["package"], module=task["module"])
        results[cell["code"]] = {"condition": cell["condition"],
                                 "import_error": result["import_error"],
                                 "checks": {cid: e["ok"]
                                            for cid, e in result["checks"].items()}}

    (out_dir / "scores.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8", newline="\n")

    conv = [c for c in order if kinds[c] == "conventional"]
    func = [c for c in order if kinds[c] == "functional"]

    def rate(condition, checks):
        cells = [r for r in results.values() if r["condition"] == condition]
        if not cells:
            return 0.0, 0, 0
        passed = sum(1 for r in cells for c in checks if r["checks"].get(c))
        total = len(cells) * len(checks)
        return 100.0 * passed / total, passed, total

    print("\nPER SAMPLE")
    for code, r in results.items():
        p = sum(1 for c in conv if r["checks"].get(c))
        f = sum(1 for c in func if r["checks"].get(c))
        flag = "  IMPORT ERROR: " + str(r["import_error"]) if r["import_error"] else ""
        print("  {:<6} {:<7} functional {}/{}  conventional {}/{}{}".format(
            code, r["condition"], f, len(func), p, len(conv), flag))

    print("\nPOOLED")
    for condition in ("none", "oracle"):
        cr, cp, ct = rate(condition, conv)
        fr, fp, ft = rate(condition, func)
        print("  {:<7} functional {}/{} ({:.1f}%)   conventional {}/{} ({:.1f}%)".format(
            condition, fp, ft, fr, cp, ct, cr))

    none_rate = rate("none", conv)[0]
    oracle_rate = rate("oracle", conv)[0]
    lift = oracle_rate - none_rate

    print("\nPER CONVENTION")
    print("  {:<34} {:>6} {:>7} {:>6}".format("check", "none", "oracle", "gap"))
    gaps = {}
    for c in conv:
        n = rate("none", [c])[0]
        o = rate("oracle", [c])[0]
        gaps[c] = o - n
        print("  {:<34} {:>5.0f}% {:>6.0f}% {:>+6.0f}".format(c, n, o, o - n))

    big = [c for c, g in gaps.items() if g >= 40]
    print("\nTHRESHOLDS, from docs/prediction-F003.md")
    print("  primary    lift {:+.1f} vs +15.0          {}".format(
        lift, "MET" if lift >= 15 else "MISSED"))
    print("  secondary  {} convention(s) with a gap >= 40 vs 2   {}".format(
        len(big), "MET" if len(big) >= 2 else "MISSED"))
    if big:
        print("             " + ", ".join(sorted(big)))
    print("\n  VERDICT: {}".format(
        "fixture ACCEPTED" if (lift >= 15 and len(big) >= 2) else "fixture REJECTED"))
    print("\nSources have not been read by this script. Read every SOURCES "
          "section before believing any of the above.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prepare", metavar="RUN")
    ap.add_argument("--collect", metavar="RUN")
    ap.add_argument("--samples", type=int, default=5)
    args = ap.parse_args()
    if args.prepare:
        return prepare(args.prepare, args.samples)
    if args.collect:
        return collect(args.collect)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
