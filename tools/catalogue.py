#!/usr/bin/env python3
"""catalogue.py -- what can be recommended, and what is known about each one.

    python tools/catalogue.py --scan               # local catalogue, not committed
    python tools/catalogue.py --publish            # public entries only, committed
    python tools/catalogue.py --check              # CI: no unearned "proven"

THE QUESTION THIS ANSWERS

"If `skills/` is empty, what does a recommender recommend?" Nothing here, is the
short answer -- and that was always the design. `skills/` is the shelf for
skills THIS repository has proven. The catalogue a recommender draws on is
mostly other people's work: 31 skills across the official plugin marketplace on
this machine, the built-in Anthropic skills, and whatever `SearchSkills` finds
in an org catalogue. A recommender does not need to own a skill to point at it.

WHAT IS ACTUALLY MISSING, AND WHY THIS FILE IS SHORT

`claude-automation-recommender` (in the `claude-code-setup` plugin) already
scans a codebase and recommends skills, plugins, hooks, subagents and MCP
servers, and the harness ships SearchSkills / SuggestSkills / SearchPlugins /
SuggestPluginInstall. Recommending is solved. Three things are not:

  1. NOTHING CARRIES EVIDENCE. Every recommendation anywhere is an assertion.
     "Recommended: frontend-design" and "recommended: <thing we measured at +40
     against a control>" render identically, and so do "recommended: <thing we
     measured and found no effect from>". This repository is the only place
     that has run the measurements, so it is the only place that can attach the
     label.

  2. THE LISTS ARE HAND-MAINTAINED. `skills-reference.md` is a markdown table
     of plugin names. It goes stale silently. This scans what is installed.

  3. NEGATIVE EVIDENCE HAS NOWHERE TO GO. 116 blind subagents found no effect
     from the 270 agency-agents bodies. That is a real result about real
     artifacts and there is no field anywhere to record it against them, so the
     next person rediscovers it.

A LABEL IS NOT A RANKING

`shipped-unmeasured` is not an insult and `proven-here` is not an endorsement
for every context. The labels say who measured what, against which control,
and nothing more. Ranking is a separate job and needs a project to rank for.

PRIVACY

`--scan` reads what is installed on this machine, which can include private or
org marketplaces. That output is gitignored. `--publish` emits only entries
from sources marked public in `eval/evidence/sources.json`, and that is the one
that gets committed -- this repository is public.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = REPO_ROOT / "eval" / "evidence" / "sources.json"
LOCAL = REPO_ROOT / "eval" / "evidence" / "catalogue.local.json"
PUBLIC = REPO_ROOT / "eval" / "evidence" / "catalogue.json"

MARKETPLACES = Path.home() / ".claude" / "plugins" / "marketplaces"

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def _front(path: Path):
    """name and description from a SKILL.md, without a YAML dependency."""
    text = path.read_text(encoding="utf-8", errors="replace")
    m = FRONTMATTER.match(text)
    block = m.group(1) if m else ""
    out = {}
    key = None
    for line in block.splitlines():
        m2 = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m2:
            key = m2.group(1)
            out[key] = m2.group(2).strip().strip('"')
        elif key and line.startswith(" "):
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def load_sources():
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))["sources"]


def classify(rel_path: str, sources):
    """First matching rule wins, so order in sources.json is meaningful.

    PREFIX, not substring. The first version used `in` and labelled all 31
    marketplace skills `proven-here`, because every one of their paths contains
    "/skills/" and that was the first rule. --check caught it on the first run.

    That is the third loose matcher this project has shipped -- after a
    proposal gate that counted adjacent phrases and missed keyword stuffing,
    and a prose detector that matched normative words and missed "Every current
    entry point validates through here". The pattern is worth naming: a matcher
    written against the cases you have in mind, tested only on those cases.
    """
    for rule in sources:
        if rel_path.startswith(rule["match"]):
            return rule
    return {"status": "unproven", "public": False,
            "citation": "no evidence recorded"}


def _result_figures(skill_dir: Path):
    """Whatever a RESULT.md claims, so a bare assertion is visible as one."""
    result = skill_dir / "RESULT.md"
    if not result.exists():
        return None
    text = result.read_text(encoding="utf-8", errors="replace")
    return {
        "names_a_comparison": any(k in text for k in ("oracle", "without_skill",
                                                      "lift", "captured")),
        "run": (re.search(r"\b(F\d{3}|[A-Z][A-Z0-9_-]{2,})\b", text) or
                [None, ""])[1] if re.search(r"\b(F\d{3})\b", text) else "",
        "chars": len(text),
    }


def scan():
    sources = load_sources()
    entries = []

    # Installed plugin skills.
    if MARKETPLACES.is_dir():
        for skill_md in sorted(MARKETPLACES.rglob("skills/*/SKILL.md")):
            rel = skill_md.relative_to(MARKETPLACES.parent).as_posix()
            front = _front(skill_md)
            rule = classify(rel, sources)
            entries.append({
                "name": front.get("name") or skill_md.parent.name,
                "description": front.get("description", "")[:400],
                "source": rel.rsplit("/skills/", 1)[0],
                "kind": "plugin-skill",
                "status": rule["status"],
                "citation": rule.get("citation", ""),
                "public": bool(rule.get("public")),
            })

    # This repository's own shelves.
    for shelf, kind in (("skills", "proven"), ("candidates", "candidate"),
                        ("quarry", "quarry")):
        root = REPO_ROOT / shelf
        if not root.is_dir():
            continue
        for entry in sorted(p for p in root.iterdir() if p.is_dir()):
            rule = classify(shelf + "/", sources)
            figures = _result_figures(entry)
            status = rule["status"]
            if rule.get("requires_result") and not (
                    figures and figures["names_a_comparison"]):
                status = "unproven"
            entries.append({
                "name": entry.name,
                "description": (_front(entry / "SKILL.md").get("description", "")
                                if (entry / "SKILL.md").exists() else "")[:400],
                "source": shelf + "/" + entry.name,
                "kind": kind,
                "status": status,
                "citation": rule.get("citation", ""),
                "public": bool(rule.get("public")),
                "result": figures,
            })
    return entries


def _write(path: Path, entries):
    tally = {}
    for e in entries:
        tally[e["status"]] = tally.get(e["status"], 0) + 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"count": len(entries), "by_status": tally, "entries": entries},
        indent=2) + "\n", encoding="utf-8", newline="\n")
    return tally


def report(tally, where):
    print("wrote {} ({} entries)".format(where, sum(tally.values())))
    for status, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print("  {:<22} {}".format(status, n))


def check(entries=None) -> int:
    """No entry may claim to be proven without a RESULT.md naming a comparison."""
    entries = entries if entries is not None else scan()
    unearned = [e for e in entries if e["status"] == "proven-here"
                and not (e.get("result") or {}).get("names_a_comparison")]
    for e in unearned:
        print("FAILED: {} is labelled proven-here with no RESULT.md naming a "
              "control".format(e["source"]), file=sys.stderr)
    if unearned:
        return 1
    proven = [e for e in entries if e["status"] == "proven-here"]
    print("PASSED: {} entr{} labelled proven-here, all naming a control."
          .format(len(proven), "y" if len(proven) == 1 else "ies"))
    if not proven:
        print("        Zero is the honest number today. Three fixtures were "
              "rejected;\n        see docs/findings.md.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        return check()
    entries = scan()
    if args.publish:
        public = [e for e in entries if e["public"]]
        report(_write(PUBLIC, public), PUBLIC.relative_to(REPO_ROOT).as_posix())
        print("\n{} local entr{} withheld as non-public.".format(
            len(entries) - len(public),
            "y" if len(entries) - len(public) == 1 else "ies"))
        return 0
    if args.scan:
        report(_write(LOCAL, entries), LOCAL.relative_to(REPO_ROOT).as_posix())
        print("\nNot committed: this lists what is installed on this machine.")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
