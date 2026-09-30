# Touchstone

[![Check](https://github.com/jasperntc/touchstone/actions/workflows/check.yml/badge.svg?branch=main)](https://github.com/jasperntc/touchstone/actions/workflows/check.yml)

*A collection of skills, none of which is here on anybody's say-so.*

**Status: finished. `skills/` is empty, and that is the result.**

A touchstone is the dark stone a jeweller rubs gold against: the streak it
leaves tells you the purity, whatever the piece looks like. The stone is the
instrument, not the inventory — which turned out to be the right way round,
because the instrument is the only part that earned its keep.

---

## The conclusion, first

Five pre-registered experiments, **52 blind subagents** here and **174** in the
predecessor. Nothing ever entered `skills/`.

> **A skill is not free.** Two different skills carrying the same three facts
> both improved the task they were written for and both made an **unrelated**
> task measurably worse — by −13.3 and −8.3 points, from opposite causes.

That finding undercuts this repository's own premise. Touchstone was built to
be a *curated collection you install*. A collection is many skills loaded at
once, which is the worst configuration under its own strongest result. The
instrument recommended against the product it was built to serve, so the
product was not built.

That is what a working instrument looks like. The whole point was to avoid
shipping unproven content, and it did — by never letting anything through.

## What was measured

| | fixture | subagents | headline | verdict |
|---|---|---:|---|---|
| **F001** | 6 files, 6 conventions | 6 | oracle lift **−26.7** | task rejected |
| **F002** | 52 files, 8 conventions | 6 | **+12.5** vs +15 | task rejected |
| **F003** | 54 files, 10 conventions | 10 | **+12.0** vs +15, 1 discriminator vs 2 | task rejected |
| **F004** | absent information | 15 | lift **+53.3**, capture **100%**, harm **−13.3** | skill not proven |
| **F005** | leaks repaired, skill v2 | 15 | lift **+100**, capture **136%**, harm **−8.3** | skill not proven |

Predecessor (`agency-agents`, 270 agent files): **116 blind subagents across two
model tiers found no measurable effect** from the agent bodies. Selection over
them did work — 57/58, literal reachability 70.18%.

Full write-ups, including every instrument defect: **[docs/findings.md](docs/findings.md)**.

## The five things worth taking away

**1. A skill installs a disposition, not just content.** F004's skill argued
vividly that data gets lost unnoticed; every sample carrying it then refused to
truncate a list *in a different package*, using the skill's own word —
"silently drop". F005 removed the argument and that harm vanished entirely.

**2. A scope disclaimer is not neutral.** F005's skill closed with "these rules
are not a general position on pagination, on ordering… follow this codebase's
own conventions." On the unrelated task, `ids.valid` usage fell 5/5 → **1/5**
and sorting 5/5 → **3/5**. Naming a topic to disclaim it puts the topic in
play, and "follow the codebase's conventions" points at the *majority pattern*
rather than the invariant the codebase *states* about itself.

**3. One sentence of prompt did most of what a conventions skill was for.**
Adding *"anything this brief does not pin down, match to the rest of the
codebase"* to a task closed most of the gap. F002's controls missed the
ordering convention; F003's got it five times out of five. Reach for the
sentence before proposing the skill.

**4. Frontier models read a codebase and match it.** F003's control scored
**88%** on ten house conventions it was told nothing about, including two
demonstrated in only 5 of 27 modules. The one rule it declined, it had found
and rejected on reasoning. Private project context is not the moat it looks
like.

**5. Check what your example values announce.** F004's `a1` measured **+0**
because the client docstring read `{"status": "ok", ...}` — a field whose value
is spelled out tells the reader other values exist. Deleting it took `a1` from
+0 to +100. The example body was the answer key.

## The apparatus, if you want to reuse it

`skill-creator` (in `anthropics/claude-plugins-official`) runs the evaluation
loop: with-skill and baseline subagents together, a grader, mean/stddev/delta,
a blind comparator, description tuning with a held-out split. **Use it.** A
parallel harness here was rebuilding that and was deleted.

What this repository adds, and skill-creator has no equivalent for:

| | |
|---|---|
| **`prereg.py --harm-eval`** | a held-out task the skill should not touch, scored separately. **This is the only novel instrument here** and it is what caught F004 and F005. |
| `prereg.py` oracle gate | if handing the answer over outright does not beat the control, the **task** is rejected before any skill is written |
| `prereg.py` capture gate | how much of the oracle's proven headroom the *packaged* skill actually delivers |
| `prereg.py` threshold | refuses to score a run whose registration is uncommitted, edited, or later than the numbers |
| `stage.py` | serves the fixture where no `.git` resolves — a control that can run `git show` is not a control |
| `stage.py --audit` | flags prose that *states* a rule instead of demonstrating it |
| `tools/catalogue.py` | evidence labels: `proven-here` / `shipped-unmeasured` / `measured-no-effect` / `unproven` |

Everything is deterministic and free; the blind runs are the only expensive
part. See **[docs/how-a-skill-gets-proven.md](docs/how-a-skill-gets-proven.md)**
for the command sequence.

## When to pick this up again

Not on a schedule — on a symptom. If you hit a **recurring, project-specific
failure** that a skill could plausibly fix, run one experiment against your own
codebase. The fixture, the gates and the runbook are calibrated and it takes an
afternoon.

That is the right use of an instrument: something you pick up for a specific
question, not a programme you maintain.

## What this does not claim

- One synthetic codebase, one model tier (`claude-opus-5`), five samples per arm.
- The harm result is **n=2 runs**. It is consistent and dose-dependent, not
  conclusive.
- Nothing here tests **tool-bundling skills** — `pdf`, `xlsx`, `docx` — whose
  value is executable scripts rather than prose. That category may behave
  entirely differently. Nobody has checked.
- *"Do not build a collection"* is an inference from the harm result, not a
  measurement of a collection.

## Layout

    skills/       empty, and that is the finding
    candidates/   certis-verification -- measured twice, not proven
    eval/
      fixture/    the Meridian codebase and its generator
      tasks/      questions; key/ withheld, key/retired/ for superseded ones
      harness/    stage.py, run_checks.py, prereg.py, to_benchmark.py
      prereg/     thresholds, committed before their runs
      runs/       F003-F005 in full: prompts, assignments, answers, scores
      evidence/   the catalogue and its source rules
    docs/findings.md
