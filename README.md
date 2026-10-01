# Touchstone

[![Check](https://github.com/jasperntc/touchstone/actions/workflows/check.yml/badge.svg?branch=main)](https://github.com/jasperntc/touchstone/actions/workflows/check.yml)

**In plain terms.** Claude Code can load "skills": short written instructions
that tell the AI how to handle a particular kind of task. This project tests
whether adding one actually helps. It runs the AI three ways: without the skill,
with it, and simply handed the answer. The pass marks are committed in advance.
In the final run, F005, the skill took the AI from 0 of 15 to 15 of 15 on the
facts it carried, but made an unrelated task worse: −8.3 points against a −5
limit, so it failed ([findings](docs/findings.md)). Why it matters: a skill can
quietly cost you elsewhere, and this bench is built to catch that. Five samples
per arm can't settle how much.

Corrections to the record since it was written: **[docs/errata.md](docs/errata.md)**.
Why each part is built the way it is, and its limits:
**[docs/decisions.md](docs/decisions.md)**.
Every mistake caught while preparing this release, mine and the AI's:
**[REVIEW_LOG.md](REVIEW_LOG.md)**.

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

> **A skill is not free.** In F005 the skill improved the task it was written
> for and made an **unrelated** task worse, by −8.3 points against a −5
> tolerance. An earlier run, F004, pointed the same way, but it is unreadable
> under the harness's own rule ([errata E3](docs/errata.md)), so it isn't
> evidence.

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
| **F004** | absent information | 15 | **unreadable**: 3 of 5 controls failed the sanity floor ([E3](docs/errata.md)) | skill not proven |
| **F005** | leaks repaired, skill v2 | 15 | lift **+100**, capture **136%**, harm **−8.3** | skill not proven |

Predecessor (`agency-agents`, 270 agent files): **116 blind subagents across two
model tiers found no measurable effect** from the agent bodies. Selection over
them did work — 57/58, literal reachability 70.18%.

Full write-ups, including every instrument defect: **[docs/findings.md](docs/findings.md)**.

## Verify it yourself

Needs git and Python (checked on 3.12; standard library only). After the clone,
nothing calls a model or touches the network.

```bash
git clone https://github.com/jasperntc/touchstone.git
cd touchstone
python tools/verify.py
python -m unittest discover -s tests
```

`verify.py` re-scores every committed answer with the committed key, diffs the
regenerated results against the committed ones, and re-checks the numbers in
`docs/findings.md`. It ends with:

```
GATES      prereg.evaluate, committed vs regenerated
  F004  NOT PROVEN  headroom +53.3  lift +53.3  captured 100%  harm -13.3   agree
  F005  NOT PROVEN  headroom +73.3  lift +100.0  captured 136%  harm -8.3   agree

CLAIMS     166 checked against docs/findings.md and docs/prediction-F003.md, 0 mismatch(es)

HISTORY    checked
EVIDENCE   120 file(s) hashed before and after, 0 changed
NOT COVERED 8 item(s), listed in build/verify/report.md

VERIFIED
```

The F004 line shows the numbers re-derive. It doesn't make them evidence
([E3](docs/errata.md)).

**`verify.py` runs code that a model wrote.** It executes each committed
model-written answer under `eval/runs/` against its key: one subprocess per
answer, in a temporary copy of the fixture. It checks their imports against a
short allowlist first. That is not a sandbox. The answers run with your
permissions, so read them first if that matters to you.

The tests end with `Ran 92 tests` and `OK (skipped=1, expected failures=1)`.
Lines starting `FAILED:` come from tests checking that a check refuses what it
should. The skip is a schema check that needs the skill-creator plugin
installed. The expected failure is [E4](docs/errata.md), recorded and left
unfixed.

## The five things worth taking away

**1. A skill may install a disposition, not just content.** F004's skill argued
vividly that data gets lost unnoticed; every sample carrying it then refused to
truncate a list *in a different package*, using the skill's own word —
"silently drop". F004 is unreadable under [E3](docs/errata.md), so this is a
lead, not a result. F005 removed the argument and that pattern did not recur.

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
while the client docstring read `{"status": "ok", ...}` — a field whose value
is spelled out tells the reader other values exist. F004 is unreadable under
[E3](docs/errata.md), so that +0 isn't evidence. In F005, with the example
value deleted, every control missed `a1` and it measured **+100**.

## The apparatus, if you want to reuse it

`skill-creator` (in `anthropics/claude-plugins-official`) runs the evaluation
loop: with-skill and baseline subagents together, a grader, mean/stddev/delta,
a blind comparator, description tuning with a held-out split. **Use it.** A
parallel harness here was rebuilding that and was deleted.

What this repository adds, and skill-creator has no equivalent for:

| | |
|---|---|
| **`prereg.py --harm-eval`** | a held-out task the skill should not touch, scored separately. **This is the only novel instrument here** and it is what caught F005 (F004 is unreadable under [E3](docs/errata.md)). |
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
- The harm result rests on **one readable run**, F005: five samples per arm,
  −8.3 against a −5 tolerance, and the per-sample scores overlap (control 10–11
  of 12, skill 8–11). F004 is unreadable under [E3](docs/errata.md). Not
  conclusive.
- Nothing here tests **tool-bundling skills** — `pdf`, `xlsx`, `docx` — whose
  value is executable scripts rather than prose. That category may behave
  entirely differently. Nobody has checked.
- *"Do not build a collection"* is an inference from the harm result, not a
  measurement of a collection.

## My role

I ran this project with Claude Code as the implementer. The method came out of
working with Claude Code; I chose the thresholds, set the rule that nothing
ships unless it passes every gate, and made each call on what the evidence
showed. Claude Code wrote most of the code and drafted most of the
documentation, including docs/decisions.md. I reviewed and approved every
change.

Before release, I put guardrails around my own record: a baseline tag, CI checks
that fail if the evidence changes, gate tests proven able to fail, and
tools/verify.py, which re-derives every headline number in the F003–F005 record
from the raw answers. Those checks produced four corrections, published in
docs/errata.md. The biggest was my own call: I reported F004 without applying a
floor rule I had written before the run. REVIEW_LOG.md lists every mistake
caught during that review, mine and the AI's.

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
