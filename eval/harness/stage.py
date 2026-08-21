#!/usr/bin/env python3
"""stage.py -- serve the fixture from somewhere the answer key cannot be reached.

    python eval/harness/stage.py                 # stage, verify, print the path
    python eval/harness/stage.py --verify DIR    # re-check an existing staging
    python eval/harness/stage.py --audit         # scan prose for stated rules

WHY THIS FILE EXISTS

F002's `none/q4m` scored a perfect 8/8 on the conventional checks and said,
unprompted, that it had recovered CONVENTIONS.md from the repository's git
history. It was right to. The file had been moved out of the working tree and
then committed in the same session, so `git show <sha>:eval/fixture/...` handed
over all eight rules to a condition defined by not having them.

**Stashing the working tree is not blindness when the answer key is in the
object store.** Every run in this repository and in agency-agents before it
used that procedure, so the hole was always there and simply went unexercised
until a subagent volunteered what it had done.

The fix cannot be a rule people follow. It has to be a property of the
directory the answerer is given:

    1. the staged tree contains no .git, and no ANCESTOR of it does either,
       so `git` walking upward from the fixture finds nothing to show;
    2. the conventions file is never written to disk at all -- the oracle
       condition receives the rules in its prompt, so there is no file to find
       in any condition;
    3. the key, the calibration drafts and the generator do not travel.

`--verify` re-asserts all three against a directory that already exists, which
is what the test calls. `stage()` runs it before returning, so a staging that
cannot be verified is never handed out.

WHAT --audit IS FOR

Two of F002's five instrument defects were prose, not procedure: module
docstrings that recited the conventions, and design commentary in `_store.py`
that stated the expected answer outright. Neither is caught by anything above
-- the file is legitimately part of the fixture; it is the ENGLISH in it that
leaks.

So `--audit` reads docstrings and comments only, never code. Code that
*demonstrates* a convention is the entire point of the fixture. Prose that
*states* one is the answer key wearing a disguise.
"""
from __future__ import annotations

import argparse
import ast
import io
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "eval" / "fixture"
DEFAULT_OUT = REPO_ROOT.parent / "_touchstone_staging"

# Never copied. The first is the answer; the last would let an answerer
# regenerate the fixture and read PLAN, which labels every module's role.
NEVER_COPY = {"CONVENTIONS.md", "_build_meridian.py"}
NEVER_COPY_DIRS = {".git", "__pycache__", ".pytest_cache"}

# Terms that turn up when someone is DESCRIBING a rule rather than following
# it. Deliberately broad: --audit reports, a human judges.
PROSE_FLAGS = [
    "convention", "house rule", "house style", "always ", "never ",
    "must ", "should ", "by convention", "we use", "prefer ",
    "newest first", "newest-first", "descending", "micros are",
    "do not raise", "rule ",
]


def _git_toplevel(path: Path):
    """The repo `git` would find from `path`, or None if there is none."""
    try:
        proc = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                              cwd=str(path), capture_output=True, text=True,
                              check=False)
    except FileNotFoundError:
        raise SystemExit(
            "git is not on PATH, so isolation cannot be verified. Refusing to "
            "stage: an unverified staging is exactly the F002 failure.")
    return proc.stdout.strip() or None


def verify(out: Path):
    """Every way the answer key has been reachable, asserted against `out`."""
    problems = []
    out = out.resolve()

    if not out.is_dir():
        return ["{} does not exist".format(out)]

    # (1) git, walking upward. This is the F002 breach, stated as a check.
    top = _git_toplevel(out)
    if top is not None:
        problems.append(
            "`git` resolves to {} from the staged tree. Anything ever "
            "committed there is retrievable with `git show`, including the "
            "conventions. Stage outside every repository.".format(top))

    for d in sorted(p for p in out.rglob("*") if p.is_dir()):
        if d.name in NEVER_COPY_DIRS:
            problems.append("{}/ should not be here".format(
                d.relative_to(out).as_posix()))

    # (2) the key, the conventions, the drafts, the generator.
    for f in sorted(p for p in out.rglob("*") if p.is_file()):
        rel = f.relative_to(out).as_posix()
        if f.name in NEVER_COPY:
            problems.append("{} is the answer and must never be staged".format(rel))
        if rel.startswith("key/") or "/key/" in rel:
            problems.append("{} is a grading key".format(rel))

    # (3) the fixture itself actually arrived.
    if not (out / "meridian" / "__init__.py").exists():
        problems.append("meridian/ did not arrive -- nothing to answer against")
    return problems


def stage(out: Path, force: bool = False) -> Path:
    out = out.resolve()
    if REPO_ROOT in out.parents or out == REPO_ROOT:
        raise SystemExit(
            "refusing to stage into {}: it is inside {}, so `git show` reaches "
            "the conventions from it. That is the F002 breach exactly.".format(
                out, REPO_ROOT.name))
    if out.exists():
        if not force and any(out.iterdir()) and not (out / "meridian").exists():
            raise SystemExit(
                "refusing to overwrite non-staging directory {}".format(out))
        shutil.rmtree(str(out))
    out.mkdir(parents=True)

    shutil.copytree(
        str(FIXTURE / "meridian"), str(out / "meridian"),
        ignore=shutil.ignore_patterns(*sorted(NEVER_COPY_DIRS | NEVER_COPY)))

    problems = verify(out)
    if problems:
        for p in problems:
            print("  " + p, file=sys.stderr)
        raise SystemExit("staging failed verification; nothing was handed out.")
    return out


def _prose(path: Path):
    """Docstrings and comments. Never code."""
    found = []
    src = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return found
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef,
                             ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if doc:
                found.append((getattr(node, "lineno", 1), doc))
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            found.append((tok.start[0], tok.string))
    return found


def audit(root: Path) -> int:
    """Report English in the fixture that STATES a rule instead of following it."""
    hits = 0
    for path in sorted(root.rglob("*.py")):
        if any(part in NEVER_COPY_DIRS for part in path.parts):
            continue
        for line, text in _prose(path):
            low = text.lower()
            for flag in PROSE_FLAGS:
                if flag in low:
                    one = " ".join(text.split())
                    print("{}:{}  [{}]  {}".format(
                        path.relative_to(root).as_posix(), line,
                        flag.strip(), one[:110]))
                    hits += 1
                    break
    if hits:
        print("\n{} passage(s) to read. A fixture teaches by example; prose "
              "that names a rule is the answer key in disguise.".format(hits))
    else:
        print("No prose states a rule. The fixture demonstrates only.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--verify", metavar="DIR")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.audit:
        return audit(FIXTURE / "meridian")
    if args.verify:
        problems = verify(Path(args.verify))
        for p in problems:
            print("  " + p, file=sys.stderr)
        if problems:
            print("\nFAILED: {} way(s) to reach the answer.".format(len(problems)),
                  file=sys.stderr)
            return 1
        print("PASSED: no git above it, no key in it, fixture present.")
        return 0

    out = stage(Path(args.out), force=args.force)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
