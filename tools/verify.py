#!/usr/bin/env python3
"""verify.py -- re-derive docs/findings.md from the committed record, offline.

    python tools/verify.py                  # git-history checks may be skipped
    python tools/verify.py --require-git    # CI: a skipped check is a failure

WHAT THIS DOES

Every number in docs/findings.md came from blind answers that are committed
under eval/runs/, scored by keys committed under eval/tasks/key/, against gates
committed under eval/prereg/. This re-runs that chain from the answers up and
stops at the prose:

  1. re-score    every committed answer with the committed key, and regenerate
                 scores.json (F003) or benchmark.json + floor.json (F004, F005)
                 into build/verify/
  2. compare     each regenerated artifact with the committed one, field by
                 field, error text included
  3. gates       prereg.evaluate() on the committed AND the regenerated
                 benchmark; the two must agree
  4. claims      each headline number in findings.md, read from its own line,
                 against the value the regenerated artifacts produce
  5. history     the registration is older than the result it judges (needs
                 full git history; see --require-git)

No model is called and nothing touches the network. The only code executed is
the committed answers, the fixture and the keys, and all three are scanned for
imports outside a short allowlist before anything runs.

WHAT IT NEVER DOES

Write into the evidence. eval/runs/, eval/prereg/, eval/tasks/key/ and
docs/findings.md are hashed before and after, ignored files included, and any
difference fails the run. Keys and answers are scored from byte-identical
copies under build/verify/, because run_checks execs the key from wherever
KEYS points and its `-I` subprocess ignores PYTHONDONTWRITEBYTECODE -- scoring
in place would drop __pycache__ into eval/tasks/key/, which is gitignored and
so invisible to a `git status` guard.

eval/harness/ is imported, not run and not edited. prereg.py and
to_benchmark.py are never invoked as scripts: the first writes eval/prereg/ and
the second, pointed at eval/runs/, overwrites benchmark.json. Only two module
globals are repointed -- run_checks.KEYS and run_checks.TASKS -- which is the
same move tests/test_prereg.py makes with prereg's.

WHAT IT CANNOT CHECK

F001 and F002 were never committed as answers. Claims read out of transcripts
("four of five oracle samples read 'again' as 'twice'") and counts taken over
the fixture rather than the runs are listed in the report as not covered.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

# Before the harness is imported: nothing this process loads may leave
# bytecode behind, least of all next to a key.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "eval" / "harness"))

import prereg as pr  # noqa: E402
import run_checks as rc  # noqa: E402
import to_benchmark as tb  # noqa: E402

OUT = REPO_ROOT / "build" / "verify"
FINDINGS = "docs/findings.md"
EVIDENCE = ("eval/runs", "eval/prereg", "eval/tasks/key", FINDINGS)

# The key each task was scored with. t004 was retired after F004 and kept
# "so that run stays reproducible" (its own docstring); it is copied, not moved.
KEY_SOURCES = {
    "t002": "eval/tasks/key/t002.py",
    "t004": "eval/tasks/key/retired/t004.py",
    "t005": "eval/tasks/key/t005.py",
}
# Where each task's answer lives inside a staged tree. t002 and t005 are
# cross-checked against eval/tasks/tasks.jsonl; t004 left that file when it was
# retired, and eval/runs/F004/README.md names meridian/compliance/reverify.py.
TASK_PLACES = {
    "t002": ("accounts", "adjustments.py"),
    "t004": ("compliance", "reverify.py"),
    "t005": ("compliance", "reverify.py"),
}
# Task order as it stood in tasks.jsonl when each run was scored; `eval_id` in
# benchmark.json is that position.
RUN_TASKS = {"F004": ("t002", "t004"), "F005": ("t002", "t005")}

# Strings rewritten in regenerated artifacts before they are compared: exact
# (regenerated, committed) pairs only, never a pattern. Empty, because no
# committed benchmark.json, floor.json or scores.json records a path of any
# kind -- no drive letter, no _touchstone_staging, no touchstone-* scratch
# directory, no backslash. If a regenerated file ever carries one, that is a
# difference and is reported as one.
SUBSTITUTIONS: tuple = ()

# Top-level imports the executed code may make. Anything else -- socket, http,
# urllib, subprocess, a third-party client -- fails the run before it scores.
ALLOWED_IMPORTS = {
    "__future__", "meridian", "abc", "ast", "collections", "copy",
    "dataclasses", "datetime", "decimal", "enum", "functools", "inspect",
    "itertools", "json", "math", "operator", "re", "time", "typing",
}

ARMS = ("without_skill", "oracle", "with_skill")
WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
         "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}

NOT_COVERED = [
    "F001 (findings.md:9-79): no answers were committed for this run.",
    "F002 (findings.md:83-166): no answers were committed for this run.",
    "F003 `54 files each, byte-identical` (findings.md:297-298): the staged "
    "trees were not kept.",
    "F003 `27 current modules ... 5 sort, 5 cap and 3 filter zeros` "
    "(findings.md:256-257) and `22-of-25` (findings.md:242): counts over the "
    "fixture, not over the runs.",
    "F003 quoted rationales and `Four of the five controls raised the "
    "zero-amount filter` (findings.md:210): read from answer transcripts.",
    "F004 `All five controls checked it unprompted` (findings.md:422) and "
    "`Every single sample flagged this gap` (findings.md:429): transcripts.",
    "F005 `Four of five controls never looked for status` (findings.md:501) "
    "and `four of five oracle samples read \"again\" as \"twice in one pass\"` "
    "(findings.md:510-511): transcripts.",
    "F005 `isinstance, used by 24 of 27 modules` (findings.md:552): a count "
    "over the fixture.",
]


# --------------------------------------------------------------------------
# plumbing


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def inside_out(path: Path) -> Path:
    """Every write goes through here: refuse anything outside build/verify/."""
    resolved = path.resolve()
    if OUT.resolve() not in resolved.parents and resolved != OUT.resolve():
        raise SystemExit("refusing to write outside build/verify/: {}".format(
            resolved))
    return resolved


def copy_bytes(src: Path, dst: Path) -> None:
    """Copy content only. copy2 would carry the evidence's read-only bit into
    build/, and the next run could not clear it on Windows."""
    dst = inside_out(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    if sha256(src) != sha256(dst):
        raise SystemExit("copy of {} is not byte-identical".format(rel(src)))


def write_json(path: Path, data) -> None:
    path = inside_out(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8",
                    newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot() -> dict:
    """Hash every file on disk under the evidence paths, ignored ones too."""
    out = {}
    for entry in EVIDENCE:
        root = REPO_ROOT / entry
        if root.is_file():
            out[entry] = sha256(root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for name in sorted(filenames):
                p = Path(dirpath) / name
                out[rel(p)] = sha256(p)
    return out


def fresh_out() -> None:
    def clear_readonly(func, path, _exc):
        os.chmod(path, stat.S_IWRITE)
        func(path)
    if OUT.exists():
        if sys.version_info >= (3, 12):
            shutil.rmtree(OUT, onexc=clear_readonly)
        else:
            shutil.rmtree(OUT, onerror=clear_readonly)
    OUT.mkdir(parents=True)


def load_json(relpath: str):
    return json.loads((REPO_ROOT / relpath).read_text(encoding="utf-8"))


def pct(passed: int, total: int) -> float:
    return 100.0 * passed / total if total else 0.0


def check_id(key, prefix: str) -> str:
    """The one check id in `key` starting with `prefix` + '_'."""
    ids = [c["id"] for c in key.CHECKS if c["id"].startswith(prefix + "_")]
    if len(ids) != 1:
        raise SystemExit("expected one check starting {!r}, found {}".format(
            prefix, ids))
    return ids[0]


# --------------------------------------------------------------------------
# 0. what may run


def scan_imports(files) -> list:
    problems = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            elif (isinstance(node, ast.Call)
                  and isinstance(node.func, ast.Name)
                  and node.func.id == "__import__"):
                names = ["__import__()"]
            for name in names:
                if name.split(".")[0] not in ALLOWED_IMPORTS:
                    problems.append("{}:{} imports {}".format(
                        rel(path), node.lineno, name))
    return problems


def executed_code() -> list:
    files = []
    for run in ("F003", "F004", "F005"):
        files += sorted((REPO_ROOT / "eval" / "runs" / run / "answers")
                        .glob("*.py"))
    files += sorted((REPO_ROOT / "eval" / "fixture" / "meridian").rglob("*.py"))
    files += [REPO_ROOT / p for p in KEY_SOURCES.values()]
    return files


# --------------------------------------------------------------------------
# 1. re-score


def point_harness_at_copies(run: str, tasks_rows) -> None:
    keys = OUT / "keys"
    for task, src in KEY_SOURCES.items():
        copy_bytes(REPO_ROOT / src, keys / (task + ".py"))
    rc.KEYS = inside_out(keys)
    tasks = inside_out(OUT / run / "tasks.jsonl")
    tasks.parent.mkdir(parents=True, exist_ok=True)
    tasks.write_text("".join(json.dumps(r, sort_keys=True) + "\n"
                             for r in tasks_rows),
                     encoding="utf-8", newline="\n")
    rc.TASKS = tasks


def task_rows(task_ids) -> list:
    current = {t["task"]: t for t in
               (json.loads(line) for line in
                (REPO_ROOT / "eval/tasks/tasks.jsonl").read_text(
                    encoding="utf-8").splitlines() if line.strip())}
    rows = []
    for tid in task_ids:
        package, module = TASK_PLACES[tid]
        if tid in current and (current[tid]["package"], current[tid]["module"]) \
                != (package, module):
            raise SystemExit("{} sits at {}/{} in tasks.jsonl, not {}/{}".format(
                tid, current[tid]["package"], current[tid]["module"],
                package, module))
        rows.append({"task": tid, "package": package, "module": module})
    return rows


def rescore_f003() -> dict:
    manifest = load_json("eval/runs/F003/manifest.json")
    package, module = TASK_PLACES["t002"]
    point_harness_at_copies("F003", task_rows(["t002"]))
    out = {}
    for cell in manifest["cells"]:
        src = REPO_ROOT / "eval/runs/F003/answers" / (cell["code"] + ".py")
        answer = OUT / "F003" / "answers" / (cell["code"] + ".py")
        copy_bytes(src, answer)
        result = rc.score(answer, cell["task"], package=package, module=module)
        out[cell["code"]] = {
            "condition": cell["condition"],
            "import_error": result["import_error"],
            "checks": {cid: bool(c["ok"]) for cid, c in result["checks"].items()},
        }
    write_json(OUT / "F003" / "scores.json", out)
    return out


def rescore_benchmark(run: str) -> tuple:
    spec = load_json("eval/prereg/{}.json".format(run))
    assign = load_json("eval/runs/{}/assign.json".format(run))
    tasks = RUN_TASKS[run]
    point_harness_at_copies(run, task_rows(tasks))

    staging = OUT / run / "staging"
    seen = set()
    for src in sorted((REPO_ROOT / "eval/runs" / run / "answers").glob("*.py")):
        config, code, task = src.stem.split("-")
        if assign.get(code) != config:
            raise SystemExit("{}: arm in the filename is {!r}, assign.json says "
                             "{!r}".format(rel(src), config, assign.get(code)))
        if task not in tasks:
            raise SystemExit("{}: task {} is not part of {}".format(
                rel(src), task, run))
        package, module = TASK_PLACES[task]
        copy_bytes(src, staging / code / "meridian" / package / module)
        seen.add((code, task))
    missing = sorted({(c, t) for c in assign for t in tasks} - seen)
    if missing:
        raise SystemExit("{}: no committed answer for {}".format(run, missing))

    out = inside_out(OUT / run / "benchmark.json")
    log = io.StringIO()
    with contextlib.redirect_stdout(log):
        tb.build(staging, assign, out, spec["harm_eval"])
    inside_out(OUT / run / "to_benchmark.log").write_text(
        log.getvalue(), encoding="utf-8", newline="\n")
    bench = json.loads(out.read_text(encoding="utf-8"))
    floor = json.loads((out.parent / "floor.json").read_text(encoding="utf-8"))
    return spec, assign, bench, floor


# --------------------------------------------------------------------------
# 2. compare


def substitute(value, counter):
    if isinstance(value, str):
        for regenerated, committed in SUBSTITUTIONS:
            n = value.count(regenerated)
            if n:
                counter[0] += n
                value = value.replace(regenerated, committed)
        return value
    if isinstance(value, list):
        return [substitute(v, counter) for v in value]
    if isinstance(value, dict):
        return {k: substitute(v, counter) for k, v in value.items()}
    return value


def differences(committed, regenerated, path="$"):
    if type(committed) is not type(regenerated):
        yield path, committed, regenerated
    elif isinstance(committed, dict):
        for k in sorted(set(committed) | set(regenerated)):
            if k not in committed or k not in regenerated:
                yield ("{}.{}".format(path, k), committed.get(k, "<absent>"),
                       regenerated.get(k, "<absent>"))
            else:
                yield from differences(committed[k], regenerated[k],
                                       "{}.{}".format(path, k))
    elif isinstance(committed, list):
        if len(committed) != len(regenerated):
            yield ("{}.length".format(path), len(committed), len(regenerated))
        for i, (a, b) in enumerate(zip(committed, regenerated)):
            yield from differences(a, b, "{}[{}]".format(path, i))
    elif committed != regenerated:
        yield path, committed, regenerated


def compare(committed_path: str, regenerated) -> dict:
    counter = [0]
    regenerated = substitute(regenerated, counter)
    diffs = list(differences(load_json(committed_path), regenerated))
    return {"artifact": committed_path, "ok": not diffs,
            "differences": len(diffs), "substitutions": counter[0],
            "first_differences": [
                {"path": p, "committed": a, "regenerated": b}
                for p, a, b in diffs[:20]]}


# --------------------------------------------------------------------------
# 3. gates


GATE_FIELDS = ("verdict", "headroom", "lift", "captured", "harm_delta",
               "ceiling_ok", "lift_ok", "spread_ok", "captured_ok", "harm_ok")


def gate_summary(ev: dict) -> dict:
    out = {k: ev.get(k) for k in GATE_FIELDS}
    out["discriminating"] = [list(k) for k in ev.get("discriminating", [])]
    return out


# --------------------------------------------------------------------------
# 4. claims


class Claims:
    """Each claim reads its expected value off findings.md itself.

    A table claim parses one cell of one row; a prose claim matches a pattern
    over a line range. Numbers compare at the precision the document displays
    them, so "46.7%" matches 46.666... and "+53.3" matches 53.333...; words
    compare exactly. Nothing here is a transcribed constant.
    """

    def __init__(self, docs: dict):
        self.docs = docs
        self.rows = []

    def _line(self, doc, n):
        return self.docs[doc][n - 1]

    @staticmethod
    def _clean(text):
        return re.sub(r"\s+", " ", text.replace("**", "")).strip()

    @staticmethod
    def _numbers(text):
        return re.findall(r"[+-]?\d+(?:\.\d+)?", text.replace("\u2212", "-"))

    @staticmethod
    def _same(shown, value) -> bool:
        if isinstance(value, str):
            return shown == value
        if shown.lower() in WORDS:
            return WORDS[shown.lower()] == value
        shown = shown.replace("\u2212", "-")
        places = len(shown.split(".")[1]) if "." in shown else 0
        try:
            return float(shown) == float("{:.{}f}".format(value, places))
        except ValueError:
            return False

    def _add(self, cid, where, source, shown, computed, ok, note=""):
        self.rows.append({"id": cid, "where": where, "source": source,
                          "shown": shown, "computed": computed, "ok": ok,
                          "note": note})

    def cell(self, cid, line, index, expected, source, doc=FINDINGS):
        """`expected`: a word, or a list of numbers in the order shown."""
        raw = self._line(doc, line)
        cells = [self._clean(c).replace("`", "")
                 for c in raw.strip().strip("|").split("|")]
        where = "{}:{}".format(doc, line)
        if index >= len(cells):
            self._add(cid, where, source, raw.strip(), expected, False,
                      "row has no cell {}".format(index))
            return
        shown = cells[index]
        if isinstance(expected, str):
            ok = shown == expected
        else:
            nums = self._numbers(shown)
            ok = len(nums) == len(expected) and all(
                self._same(n, v) for n, v in zip(nums, expected))
        self._add(cid, where, source, shown, expected, ok)

    def header(self, cid, line, expected_cells, doc=FINDINGS):
        raw = self._line(doc, line)
        cells = [self._clean(c).replace("`", "")
                 for c in raw.strip().strip("|").split("|")]
        self._add(cid, "{}:{}".format(doc, line), "column order", " | ".join(cells),
                  " | ".join(expected_cells), cells == list(expected_cells))

    def prose(self, cid, lo, hi, pattern, expected, source, doc=FINDINGS):
        """`expected`: one value per group; a callable is a predicate."""
        text = self._clean(" ".join(self.docs[doc][lo - 1:hi]))
        where = "{}:{}".format(doc, lo if lo == hi else "{}-{}".format(lo, hi))
        m = re.search(pattern, text)
        if not m:
            self._add(cid, where, source, text[:160], expected, False,
                      "pattern not found: " + pattern)
            return
        groups = list(m.groups())
        ok = len(groups) == len(expected)
        shown_values = []
        for g, v in zip(groups, expected):
            if callable(v):
                ok = ok and bool(v(g))
                shown_values.append(g)
            else:
                ok = ok and self._same(g, v)
                shown_values.append(g)
        computed = [v.__doc__ if callable(v) else v for v in expected]
        self._add(cid, where, source, shown_values, computed, ok)

    def fact(self, cid, where, source, shown, computed, ok, note=""):
        self._add(cid, where, source, shown, computed, ok, note)


# ---- F003


def f003_claims(cl: Claims, s3: dict) -> None:
    key = rc.load_key("t002")
    kinds = {c["id"]: c["kind"] for c in key.CHECKS}
    src = "regenerated F003 scores.json"

    def pooled(cond, kind):
        cells = [c for c in s3.values() if c["condition"] == cond]
        ids = [cid for cid, k in kinds.items() if k == kind]
        passed = sum(c["checks"][cid] for c in cells for cid in ids)
        return passed, len(cells) * len(ids)

    def rate(cond, cid):
        cells = [c for c in s3.values() if c["condition"] == cond]
        return pct(sum(c["checks"][cid] for c in cells), len(cells))

    # The bars, anchored to the prediction committed before the run.
    pred = "docs/prediction-F003.md"
    bar, min_conv, gap_bar = 15.0, 2, 40.0
    cl.prose("F003.bar.primary", 125, 125, r"≥ \+(\d+) points", [bar],
             "prediction-F003.md threshold 1", doc=pred)
    cl.prose("F003.bar.secondary", 127, 127, r"At least (\w+) conventions",
             [min_conv], "prediction-F003.md threshold 2", doc=pred)
    cl.prose("F003.bar.gap", 128, 128, r"gap of ≥ (\d+) points", [gap_bar],
             "prediction-F003.md threshold 2", doc=pred)

    cl.header("F003.arms.header", 176, ["arm", "functional", "conventional"])
    for line, cond in ((178, "none"), (179, "oracle")):
        for idx, kind in ((1, "functional"), (2, "conventional")):
            p, t = pooled(cond, kind)
            cl.cell("F003.{}.{}".format(cond, kind), line, idx, [p, t, pct(p, t)],
                    src + ", {} checks, condition {}".format(kind, cond))

    lift = pct(*pooled("oracle", "conventional")) - pct(*pooled("none", "conventional"))
    conv_ids = [cid for cid, k in kinds.items() if k == "conventional"]
    gaps = {cid: rate("oracle", cid) - rate("none", cid) for cid in conv_ids}
    wide = [cid for cid, g in gaps.items() if g >= gap_bar]
    cl.cell("F003.primary.bar", 183, 1, [bar], "prediction-F003.md:125")
    cl.cell("F003.primary.lift", 183, 2, [lift],
            src + ": pooled conventional, oracle - none")
    cl.cell("F003.primary.verdict", 183, 3, "MET" if lift >= bar else "MISSED",
            "lift vs bar")
    cl.cell("F003.secondary.label", 184, 0, [gap_bar], "prediction-F003.md:128")
    cl.cell("F003.secondary.bar", 184, 1, [min_conv], "prediction-F003.md:127")
    cl.cell("F003.secondary.count", 184, 2, [len(wide)],
            src + ": conventions with oracle - none >= {:.0f}".format(gap_bar))
    cl.cell("F003.secondary.verdict", 184, 3,
            "MET" if len(wide) >= min_conv else "MISSED", "count vs bar")

    cl.header("F003.checks.header", 191, ["check", "none", "oracle", "gap"])
    rows = {193: ["c1", "c2", "c3", "c4", "c5"], 194: ["c6"], 195: ["c7"],
            196: ["c8"], 197: ["c9"], 198: ["c10"]}
    for line, prefixes in rows.items():
        for prefix in prefixes:
            cid = check_id(key, prefix)
            for idx, value, what in ((1, rate("none", cid), "none"),
                                     (2, rate("oracle", cid), "oracle"),
                                     (3, gaps[cid], "gap")):
                cl.cell("F003.{}.{}".format(prefix, what), line, idx, [value],
                        src + ", " + cid)

    c10 = check_id(key, "c10")
    n_or = sum(1 for c in s3.values() if c["condition"] == "oracle")
    n_no = sum(1 for c in s3.values() if c["condition"] == "none")
    cl.prose("F003.c10.counts", 200, 200,
             r"(\w+) of (\w+) oracles filtered zero-amount rows\. (\w+) of (\w+) "
             r"controls did\.",
             [sum(c["checks"][c10] for c in s3.values() if c["condition"] == "oracle"),
              n_or,
              sum(c["checks"][c10] for c in s3.values() if c["condition"] == "none"),
              n_no],
             src + ", " + c10)


# ---- F004 / F005


def arm_pool(bench, task, config, check=None):
    runs = [r for r in bench["runs"]
            if r["eval_name"] == task and r["configuration"] == config]
    if check is None:
        return (sum(r["result"]["passed"] for r in runs),
                sum(r["result"]["total"] for r in runs))
    exps = [e for r in runs for e in r["expectations"] if e["text"] == check]
    return sum(1 for e in exps if e["passed"]), len(exps)


def arm_rate(bench, task, config, check=None):
    return pct(*arm_pool(bench, task, config, check))


def gate_claims(cl: Claims, run: str, lines: dict, spec, ev, src) -> None:
    bar = spec["primary_threshold_points"]
    cl.header(run + ".gates.header", lines["header"], ["gate", "bar", "measured", ""])
    rows = (
        ("task validity", lines["validity"], bar, ev["headroom"],
         "ok" if ev["headroom"] >= bar else "MISSED",
         "oracle - without_skill; bar is primary_threshold_points (the "
         "registration's note: 'Task validity gate is the +40')"),
        ("lift", lines["lift"], bar, ev["lift"],
         "MET" if ev["lift_ok"] else "MISSED", "with_skill - without_skill"),
        ("spread", lines["spread"], spec["min_discriminating_expectations"],
         len(ev["discriminating"]), "MET" if ev["spread_ok"] else "MISSED",
         "expectations with a gap >= discriminating_gap_points"),
        ("capture", lines["capture"], spec["min_captured_percent"],
         ev["captured"], "MET" if ev["captured_ok"] else "MISSED",
         "lift / headroom"),
        ("no harm", lines["harm"], -abs(spec["harm_tolerance_points"]),
         ev["harm_delta"], "ok" if ev["harm_ok"] else "REGRESSED",
         "harm eval {}, with_skill - without_skill".format(spec["harm_eval"])),
    )
    for name, line, bar_value, measured, word, how in rows:
        slug = name.replace(" ", "_")
        cl.cell("{}.gate.{}.label".format(run, slug), line, 0, name, "gate name")
        cl.cell("{}.gate.{}.bar".format(run, slug), line, 1, [bar_value],
                "eval/prereg/{}.json".format(run))
        cl.cell("{}.gate.{}.measured".format(run, slug), line, 2, [measured],
                src + ": prereg.evaluate, " + how)
        cl.cell("{}.gate.{}.word".format(run, slug), line, 3, word,
                src + ": prereg.evaluate")


def absent_table(cl, run, lines, bench, task, src):
    cl.header(run + ".absent.header", lines[0] - 2,
              ["arm", "t004 absent checks" if run == "F004" else "absent checks"])
    for line, config in zip(lines, ARMS):
        p, t = arm_pool(bench, task, config)
        cl.cell("{}.absent.{}".format(run, config), line, 1, [p, t, pct(p, t)],
                src + ", {} runs, {}".format(task, config))


def f004_claims(cl, spec, bench, ev):
    src = "regenerated F004 benchmark.json"
    k2, k4 = rc.load_key("t002"), rc.load_key("t004")
    absent_table(cl, "F004", (343, 344, 345), bench, "t004", src)
    gate_claims(cl, "F004", {"header": 347, "validity": 349, "lift": 350,
                             "spread": 351, "capture": 352, "harm": 353},
                spec, ev, src)
    cl.prose("F004.verdict", 355, 355, r"^(NOT PROVEN|PROVEN)\.", [ev["verdict"]],
             src + ": prereg.evaluate verdict")

    cl.header("F004.t002.header", 370, ["", "without_skill", "oracle", "with_skill"])
    for i, config in enumerate(ARMS, start=1):
        cl.cell("F004.t002.overall." + config, 372, i,
                [arm_rate(bench, "t002", config)], src + ", t002 runs, all checks")
    for line, prefix in ((373, "c7"), (374, "c8"), (375, "c9")):
        cid = check_id(k2, prefix)
        for i, config in enumerate(ARMS, start=1):
            cl.cell("F004.t002.{}.{}".format(prefix, config), line, i,
                    [arm_rate(bench, "t002", config, cid)], src + ", " + cid)

    def per_sample(config):
        runs = sorted((r for r in bench["runs"] if r["eval_name"] == "t002"
                       and r["configuration"] == config),
                      key=lambda r: r["run_number"])
        return ",".join(str(r["result"]["passed"]) for r in runs)
    cl.prose("F004.t002.per_sample", 377, 378,
             r"Per-sample totals were ([\d,]+) for the control against ([\d,]+) "
             r"with the skill",
             [per_sample("without_skill"), per_sample("with_skill")],
             src + ", t002 result.passed by run_number")

    c9 = check_id(k2, "c9")
    counts = [v for config in ARMS for v in arm_pool(bench, "t002", config, c9)]
    cl.prose("F004.paging", 382, 384,
             r"without_skill (\d+) of (\d+) applied it oracle (\d+) of (\d+) "
             r"with_skill (\d+) of (\d+)", counts, src + ", " + c9 + " passes")

    cl.header("F004.absent_checks.header", 413, ["", "none", "skill", "gap", ""])
    for line, prefix in ((415, "a1"), (416, "a2"), (417, "a3")):
        cid = check_id(k4, prefix)
        none = arm_rate(bench, "t004", "without_skill", cid)
        skill = arm_rate(bench, "t004", "with_skill", cid)
        for idx, value, what in ((1, none, "none"), (2, skill, "skill"),
                                 (3, skill - none, "gap")):
            cl.cell("F004.{}.{}".format(prefix, what), line, idx, [value],
                    src + ", " + cid)

    a2 = check_id(k4, "a2")
    cl.prose("F004.a2.counts", 433, 435,
             r"(\w+) of (\w+) controls skipped a `pending_review` holder, (\w+) "
             r"of (\w+) did with the skill",
             list(arm_pool(bench, "t004", "without_skill", a2))
             + list(arm_pool(bench, "t004", "with_skill", a2)),
             src + ", " + a2 + " passes")


def aborted_claim(cl):
    """Counted, never scored: findings.md says the attempt was not scored."""
    assign = load_json("eval/runs/F005/assign-aborted.json")
    written = {}
    for f in sorted((REPO_ROOT / "eval/runs/F005/partial").glob("*.py")):
        config, code, task = f.stem.split("-")
        if assign.get(code) != config:
            raise SystemExit("{}: arm {!r} but assign-aborted.json says {!r}"
                             .format(rel(f), config, assign.get(code)))
        written.setdefault(code, set()).add(task)
    complete = {config: sum(1 for c, ts in written.items()
                            if assign[c] == config and ts >= {"t002", "t005"})
                for config in ARMS}
    size = {config: sum(1 for v in assign.values() if v == config)
            for config in ARMS}
    same = (complete["oracle"], size["oracle"]) == (complete["with_skill"],
                                                    size["with_skill"])
    cl.prose("F005.aborted", 466, 467,
             r"at (\d+)/(\d+) controls and (\d+)/(\d+) in both treatment arms",
             [complete["without_skill"], size["without_skill"],
              complete["oracle"] if same else "oracle {}/{} vs with_skill {}/{}"
              .format(complete["oracle"], size["oracle"],
                      complete["with_skill"], size["with_skill"]),
              size["oracle"]],
             "eval/runs/F005/partial/ file names (both tasks written) and "
             "assign-aborted.json; not scored")


def f005_claims(cl, spec, bench, floor, ev, bench4, ev4, bug_ev):
    src = "regenerated F005 benchmark.json"
    k2, k4, k5 = rc.load_key("t002"), rc.load_key("t004"), rc.load_key("t005")
    aborted_claim(cl)
    absent_table(cl, "F005", (472, 473, 474), bench, "t005", src)
    gate_claims(cl, "F005", {"header": 476, "validity": 478, "lift": 479,
                             "spread": 480, "capture": 481, "harm": 482},
                spec, ev, src)
    failed = lambda e: sorted(g for g in ("lift_ok", "spread_ok", "captured_ok",
                                          "harm_ok") if not e[g])
    cl.prose("F005.verdict", 484, 484, r"^(NOT PROVEN|PROVEN), on the (same) gate "
             r"as F004",
             [ev["verdict"], "same" if failed(ev) == failed(ev4) else
              "failed gates differ: F004 {} vs F005 {}".format(failed(ev4),
                                                               failed(ev))],
             src + " and regenerated F004 benchmark.json: verdict, and the set of "
             "failed gates")

    cl.header("F005.repairs.header", 494, ["", "F004", "F005"])
    for line, prefix in ((496, "a1"), (497, "a2"), (498, "a3")):
        c4, c5 = check_id(k4, prefix), check_id(k5, prefix)
        g4 = (arm_rate(bench4, "t004", "with_skill", c4)
              - arm_rate(bench4, "t004", "without_skill", c4))
        g5 = (arm_rate(bench, "t005", "with_skill", c5)
              - arm_rate(bench, "t005", "without_skill", c5))
        cl.cell("F005.repairs.{}.F004".format(prefix), line, 1, [g4],
                "regenerated F004 benchmark.json, " + c4 + " gap")
        cl.cell("F005.repairs.{}.F005".format(prefix), line, 2, [g5],
                src + ", " + c5 + " gap")

    absent5 = [c["id"] for c in k5.CHECKS if c["kind"] == "absent"]
    control = {arm_rate(bench, "t005", "without_skill", cid) for cid in absent5}
    samples = len({r["run_number"] for r in bench["runs"]
                   if r["configuration"] == "without_skill"})
    cl.prose("F005.control_zero", 500, 501,
             r"the control scored (\d+)% on every one of them, in all (\w+) samples",
             [control.pop() if len(control) == 1 else
              "rates differ: {}".format(sorted(control)), samples],
             src + ", without_skill rate on each absent check")

    cl.prose("F005.capture_prose", 507, 507,
             r"`with_skill` (\S+)%, `oracle` (\S+)%, so capture reads (\S+)%",
             [arm_rate(bench, "t005", "with_skill"),
              arm_rate(bench, "t005", "oracle"), ev["captured"]],
             src + ": absent pooled rates and prereg.evaluate captured")

    functional = [c["id"] for c in k5.CHECKS if c["kind"] == "functional"]
    broken = [sum(1 for c in row["checks"]
                  if c["check"] in functional and not c["passed"])
              for row in floor if row["configuration"] == "oracle"]
    broken = [n for n in broken if n]
    cl.prose("F005.floor", 519, 519,
             r"(\w+) oracle sample also failed (\w+) functional checks",
             [len(broken), broken[0] if len(broken) == 1 else
              "per-sample failures {}".format(broken)],
             "regenerated F005 floor.json, oracle functional failures")

    cl.prose("F005.harm_prose", 525, 525, r"^(\S+) in F004, (\S+) in F005\.",
             [ev4["harm_delta"], ev["harm_delta"]],
             "prereg.evaluate harm_delta on both regenerated benchmarks")

    cl.header("F005.harm.header", 528, ["", "none", "oracle", "skill", "F004 skill"])
    for line, prefix in ((530, "c7"), (531, "c8"), (532, "c9")):
        cid = check_id(k2, prefix)
        for i, config in enumerate(ARMS, start=1):
            cl.cell("F005.t002.{}.{}".format(prefix, config), line, i,
                    [arm_rate(bench, "t002", config, cid)], src + ", " + cid)
        cl.cell("F005.t002.{}.F004_skill".format(prefix), line, 4,
                [arm_rate(bench4, "t002", "with_skill", cid)],
                "regenerated F004 benchmark.json, " + cid)

    c7, c8, c9 = (check_id(k2, p) for p in ("c7", "c8", "c9"))
    counts4 = [v for config in ARMS for v in arm_pool(bench4, "t002", config, c9)]
    counts5 = [v for config in ARMS for v in arm_pool(bench, "t002", config, c9)]
    cl.prose("F005.paging_shift", 534, 535,
             r"ran (\d+)/(\d+) → (\d+)/(\d+) → (\d+)/(\d+) is now (\d+)/(\d+) → "
             r"(\d+)/(\d+) → (\d+)/(\d+)", counts4 + counts5,
             "regenerated F004 and F005 benchmark.json, " + c9 + " passes")

    cl.prose("F005.block.header", 540, 540, r"arm (ids\.valid) (sorts) (PAGE_LIMIT)",
             ["ids.valid", "sorts", "PAGE_LIMIT"],
             "column names; read as {}, {}, {}".format(c7, c8, c9))
    block = []
    for config in ARMS:
        for cid in (c7, c8, c9):
            block += list(arm_pool(bench, "t002", config, cid))
    cl.prose("F005.block", 541, 543,
             r"without_skill (\d+)/(\d+) (\d+)/(\d+) (\d+)/(\d+) "
             r"oracle (\d+)/(\d+) (\d+)/(\d+) (\d+)/(\d+) "
             r"with_skill (\d+)/(\d+) (\d+)/(\d+) (\d+)/(\d+)", block,
             src + ", {} / {} / {} passes".format(c7, c8, c9))
    cl.prose("F005.ids_valid_fell", 553, 554,
             r"`ids\.valid` fell from (\d+)/(\d+) to (\d+)/(\d+)",
             list(arm_pool(bench, "t002", "without_skill", c7))
             + list(arm_pool(bench, "t002", "with_skill", c7)), src + ", " + c7)
    cl.prose("F005.sorting_fell", 555, 555,
             r"sorting fell from (\d+)/(\d+) to (\d+)/(\d+)",
             list(arm_pool(bench, "t002", "without_skill", c8))
             + list(arm_pool(bench, "t002", "with_skill", c8)), src + ", " + c8)

    cl.prose("F005.bug", 564, 567,
             r"all (\w+) checks pooled rather than the (\w+) absent ones, and a "
             r"(\S+) absent lift came out as (\S+) — (failing|passing) a (\S+) bar",
             [len(k5.CHECKS), len(absent5), ev["lift"], bug_ev["lift"],
              "passing" if bug_ev["lift_ok"] else "failing",
              spec["primary_threshold_points"]],
             "regenerated F005 benchmark.json + floor.json with every t005 check "
             "put back into the primary eval (the bug, reproduced in memory), "
             "through prereg.evaluate")


def with_the_bug(bench, floor, assign, task):
    """F005 as the hardcoded `!= "t004"` adapter emitted it: every check of the
    primary task pooled. Rebuilt from the regenerated benchmark (absent checks)
    and floor (functional + conventional), in memory only."""
    order = {}
    counts = {}
    for code, config in sorted(assign.items()):
        counts[config] = counts.get(config, 0) + 1
        order[(config, counts[config])] = code
    floor_by_code = {row["code"]: row for row in floor}
    buggy = copy.deepcopy(bench)
    for run in buggy["runs"]:
        if run["eval_name"] != task:
            continue
        code = order[(run["configuration"], run["run_number"])]
        extra = [{"text": c["check"], "passed": c["passed"]}
                 for c in floor_by_code[code]["checks"]]
        run["expectations"] = extra + run["expectations"]
        passed = sum(1 for e in run["expectations"] if e["passed"])
        total = len(run["expectations"])
        run["result"].update(passed=passed, failed=total - passed, total=total,
                             pass_rate=passed / total)
    return buggy


# --------------------------------------------------------------------------
# 5. history


def git(*args):
    return subprocess.run(["git", "-C", str(REPO_ROOT)] + list(args),
                          capture_output=True, encoding="utf-8",
                          errors="replace", check=False)


def history_unavailable() -> str:
    if shutil.which("git") is None:
        return "git is not installed"
    top = git("rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return "not a git checkout"
    if Path(top.stdout.strip()).resolve() != REPO_ROOT:
        return "the enclosing repository is not this one"
    if git("rev-parse", "--is-shallow-repository").stdout.strip() != "false":
        return "shallow clone; fetch full history (fetch-depth: 0)"
    return ""


def commits(path: str) -> list:
    """(sha, unix time, %ci) of every commit on HEAD touching path, newest first."""
    out = git("log", "HEAD", "--format=%H %ct %ci", "--", path).stdout
    rows = []
    for line in out.splitlines():
        sha, ct, ci = line.split(" ", 2)
        rows.append((sha, int(ct), ci))
    return rows


def history_claims(cl: Claims, skipped: list) -> None:
    why = history_unavailable()
    if why:
        skipped.append(why)
        return

    # The registration as it stands, and the arm assignment as it stands,
    # must both be older than the first commit of the result. A prereg JSON
    # must also predate the assignment and never have been edited.
    chains = (
        ("F003", "docs/prediction-F003.md", "eval/runs/F003/manifest.json",
         "eval/runs/F003/scores.json"),
        ("F004", "eval/prereg/F004.json", "eval/runs/F004/assign.json",
         "eval/runs/F004/benchmark.json"),
        ("F005", "eval/prereg/F005.json", "eval/runs/F005/assign.json",
         "eval/runs/F005/benchmark.json"),
    )
    for run, registration, assigned, result in chains:
        reg, asg, res = commits(registration), commits(assigned), commits(result)
        if not (reg and asg and res):
            skipped.append("{}: a record file has no commit on HEAD".format(run))
            continue
        reg_last, asg_last, res_first = reg[0], asg[0], res[-1]
        cl.fact("{}.registered_before_result".format(run), registration,
                "git log HEAD",
                "registration {} {}, assigned {} {}, result {} {}".format(
                    reg_last[0][:7], reg_last[2], asg_last[0][:7], asg_last[2],
                    res_first[0][:7], res_first[2]),
                "registration and assignment both older than the result",
                reg_last[1] < res_first[1] and asg_last[1] < res_first[1])
        if registration.startswith("eval/prereg/"):
            cl.fact("{}.registered_before_assignment".format(run), registration,
                    "git log HEAD", "{} vs {}".format(reg_last[2], asg_last[2]),
                    "registration older than the arm assignment",
                    reg_last[1] < asg_last[1])
            cl.fact("{}.registration_never_rewritten".format(run), registration,
                    "git log HEAD", "{} commit(s)".format(len(reg)), "1 commit",
                    len(reg) == 1)

    # findings.md:573-576 -- the F005 correction, which the prose says must be
    # checkable. Times are each commit's own %ci offset, never local time.
    adapter = commits("eval/harness/to_benchmark.py")[-1]
    t005 = commits("eval/tasks/key/t005.py")[-1]
    hours = (t005[1] - adapter[1]) // 3600

    def prefix_of(full):
        def check(shown):
            return full.startswith(shown) and len(shown) >= 7
        check.__doc__ = "prefix of " + full
        return check
    cl.prose("F005.correction_times", 573, 576,
             r"committed at `([0-9a-f]+)`, (\d\d:\d\d); t005 landed at "
             r"`([0-9a-f]+)`, (\d\d:\d\d), (\w+) hours later",
             [prefix_of(adapter[0]), adapter[2][11:16], prefix_of(t005[0]),
              t005[2][11:16], hours],
             "git log %ci: first commit of eval/harness/to_benchmark.py, first "
             "commit of eval/tasks/key/t005.py")

    design = git("show", "{}:docs/design-F004.md".format(adapter[0]))
    line = (design.stdout.splitlines()[142:143] or [""])[0]
    cl.fact("F005.correction_design_line", "docs/design-F004.md:143",
            "git show {}:docs/design-F004.md".format(adapter[0][:7]),
            line[:80], "contains 'on the absent checks'",
            "on the absent checks" in line)
    blame = git("blame", "--porcelain", "-L143,143", "HEAD", "--",
                "docs/design-F004.md").stdout.split(" ", 1)[0]
    adapter_src = git("show", "{}:eval/harness/to_benchmark.py".format(adapter[0]))
    cl.fact("F005.correction_adapter_docstring", "eval/harness/to_benchmark.py",
            "git show {}:eval/harness/to_benchmark.py".format(adapter[0][:7]),
            "docstring at the adapter's first commit",
            "says it carries 'the ABSENT checks only'",
            "ABSENT checks only" in adapter_src.stdout,
            note="design-F004.md:143 is present at {} but was last changed at "
                 "{} ({}), earlier still; findings.md:574 says both were "
                 "'committed at' {}.".format(
                     adapter[0][:7], blame[:7],
                     git("log", "-1", "--format=%ci", blame).stdout.strip(),
                     adapter[0][:7]))


# --------------------------------------------------------------------------
# report


def render(report: dict) -> str:
    lines = ["# verify", "",
             "Result: **{}**".format("VERIFIED" if report["ok"] else "MISMATCH"),
             "", "## Artifacts, regenerated vs committed", "",
             "| artifact | differences | substitutions | |", "|---|---:|---:|---|"]
    for a in report["artifacts"]:
        lines.append("| `{}` | {} | {} | {} |".format(
            a["artifact"], a["differences"], a["substitutions"],
            "ok" if a["ok"] else "MISMATCH"))
    lines += ["", "## Gates, prereg.evaluate on committed vs regenerated", "",
              "| run | agree | verdict | headroom | lift | captured | harm |",
              "|---|---|---|---:|---:|---:|---:|"]
    for run, g in sorted(report["gates"].items()):
        r = g["regenerated"]
        lines.append("| {} | {} | {} | {:+.1f} | {:+.1f} | {:.0f}% | {:+.1f} |"
                     .format(run, "yes" if g["agree"] else "NO", r["verdict"],
                             r["headroom"], r["lift"], r["captured"],
                             r["harm_delta"]))
    lines += ["", "## Claims", "",
              "| | where | shown | computed | from |", "|---|---|---|---|---|"]
    for c in report["claims"]:
        lines.append("| {} | `{}` | {} | {} | {} |".format(
            "ok" if c["ok"] else "**MISMATCH**", c["where"],
            json.dumps(c["shown"], ensure_ascii=False).replace("|", "\\|"),
            json.dumps(c["computed"], ensure_ascii=False).replace("|", "\\|"),
            (c["source"] + (" -- " + c["note"] if c["note"] else ""))
            .replace("|", "\\|")))
    lines += ["", "## Skipped", ""] + (
        ["- " + s for s in report["skipped"]] or ["- nothing"])
    lines += ["", "## Not covered", ""] + ["- " + s for s in report["not_covered"]]
    lines += ["", "## Evidence", "",
              "{} files hashed before and after; {} changed.".format(
                  report["evidence"]["files"], len(report["evidence"]["changed"]))]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--require-git", action="store_true",
                    help="fail, rather than skip, when history cannot be read")
    args = ap.parse_args()
    # findings.md is full of U+2212; a cp1252 console must not turn a
    # mismatch report into a crash.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    before = snapshot()
    problems = scan_imports(executed_code())
    if problems:
        for p in problems:
            print("REFUSED: " + p, file=sys.stderr)
        print("Code outside the import allowlist would be executed. Nothing was "
              "scored.", file=sys.stderr)
        return 1
    fresh_out()

    s3 = rescore_f003()
    spec4, assign4, bench4, floor4 = rescore_benchmark("F004")
    spec5, assign5, bench5, floor5 = rescore_benchmark("F005")

    artifacts = [
        compare("eval/runs/F003/scores.json", s3),
        compare("eval/runs/F004/benchmark.json", bench4),
        compare("eval/runs/F004/floor.json", floor4),
        compare("eval/runs/F005/benchmark.json", bench5),
        compare("eval/runs/F005/floor.json", floor5),
    ]

    gates = {}
    evs = {}
    for run, spec, bench in (("F004", spec4, bench4), ("F005", spec5, bench5)):
        committed = gate_summary(pr.evaluate(
            spec, load_json("eval/runs/{}/benchmark.json".format(run))))
        ev = pr.evaluate(spec, bench)
        evs[run] = ev
        regenerated = gate_summary(ev)
        gates[run] = {"agree": committed == regenerated, "committed": committed,
                      "regenerated": regenerated}
    bug_ev = pr.evaluate(spec5, with_the_bug(bench5, floor5, assign5, "t005"))

    docs = {d: (REPO_ROOT / d).read_text(encoding="utf-8").splitlines()
            for d in (FINDINGS, "docs/prediction-F003.md")}
    cl = Claims(docs)
    f003_claims(cl, s3)
    f004_claims(cl, spec4, bench4, evs["F004"])
    f005_claims(cl, spec5, bench5, floor5, evs["F005"], bench4, evs["F004"],
                bug_ev)
    skipped = []
    history_claims(cl, skipped)

    after = snapshot()
    changed = sorted(k for k in set(before) | set(after)
                     if before.get(k) != after.get(k))

    ok = (all(a["ok"] for a in artifacts)
          and all(g["agree"] for g in gates.values())
          and all(c["ok"] for c in cl.rows)
          and not changed
          and not (skipped and args.require_git))
    report = {
        "ok": ok, "artifacts": artifacts, "gates": gates, "claims": cl.rows,
        "skipped": skipped, "require_git": args.require_git,
        "not_covered": NOT_COVERED,
        "evidence": {"files": len(before), "changed": changed},
    }
    write_json(OUT / "report.json", report)
    inside_out(OUT / "report.md").write_text(render(report), encoding="utf-8",
                                             newline="\n")

    print("ARTIFACTS  regenerated vs committed")
    for a in artifacts:
        print("  {:<34} {:>3} difference(s), {} substitution(s)   {}".format(
            a["artifact"], a["differences"], a["substitutions"],
            "ok" if a["ok"] else "MISMATCH"))
        for d in a["first_differences"][:5]:
            print("      {}: committed {!r}, regenerated {!r}".format(
                d["path"], d["committed"], d["regenerated"]))
    print("\nGATES      prereg.evaluate, committed vs regenerated")
    for run, g in sorted(gates.items()):
        r = g["regenerated"]
        print("  {}  {:<10}  headroom {:+.1f}  lift {:+.1f}  captured {:.0f}%  "
              "harm {:+.1f}   {}".format(run, r["verdict"], r["headroom"],
                                         r["lift"], r["captured"], r["harm_delta"],
                                         "agree" if g["agree"] else "DISAGREE"))
    bad = [c for c in cl.rows if not c["ok"]]
    print("\nCLAIMS     {} checked against {} and docs/prediction-F003.md, "
          "{} mismatch(es)".format(len(cl.rows), FINDINGS, len(bad)))
    for c in bad:
        print("  MISMATCH {}  {}: shown {}, computed {}{}".format(
            c["where"], c["id"],
            json.dumps(c["shown"], ensure_ascii=False),
            json.dumps(c["computed"], ensure_ascii=False),
            "  ({})".format(c["note"]) if c["note"] else ""))
    print("\nHISTORY    " + ("; ".join(skipped) + ("   FAILED (--require-git)"
                                                    if args.require_git else
                                                    "   skipped")
                             if skipped else "checked"))
    print("EVIDENCE   {} file(s) hashed before and after, {} changed{}".format(
        len(before), len(changed), "" if not changed else ": " + ", ".join(changed)))
    print("NOT COVERED {} item(s), listed in build/verify/report.md".format(
        len(NOT_COVERED)))
    print("\n{}".format("VERIFIED" if ok else "MISMATCH -- see build/verify/report.md"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
