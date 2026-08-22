# F005 — aborted mid-run. Not scored, and not scoreable.

**2026-08-22.** All fifteen subagents were terminated by an account spend limit
while working. What reached disk:

| arm | samples with both tasks answered |
|---|---|
| `without_skill` | 4 of 5 |
| `oracle` | **0 of 5** |
| `with_skill` | **0 of 5** |

**No treatment arm produced a single complete answer, so there is no comparison
to make.** `benchmark.json` was not generated and `--verdict` was not run. A
lift computed from four controls and zero treatments is not a small result or a
noisy one; it is not a result.

## What is kept, and what it is not

`partial/` holds the twelve files that were written before the kill, labelled
by arm. They are preserved because throwing away work that cost real money to
produce is wasteful, and because the four complete `without_skill` samples are
genuine blind answers to a committed prompt against a committed fixture.

**They are not evidence on their own.** Nothing in this directory may be quoted
as a control rate, a baseline, or a comparison. A control is only a control
relative to a treatment measured beside it.

## What is unaffected

The pre-registration (`eval/prereg/F005.json`), the fixture repairs, the task,
the key, skill v2, and the three prompt arms were all committed before any
subagent was spawned and are untouched by the abort. A re-run needs no new
design work — only the fleet.

## Re-running it

The fixture and prompts are byte-identical to what these samples saw, so a
re-run is a re-run rather than a new experiment. Three options, and the choice
is about cost, not method:

- **All fifteen again on `claude-opus-5`.** Cleanest. Every arm produced in one
  window, and directly comparable to F001–F004, which were all Opus.
- **Only the missing samples, on Opus.** Cheapest Opus route. Introduces a mild
  time confound: four controls from one window, everything else from another.
  Defensible, and it must be recorded here if taken.
- **All fifteen on a cheaper tier.** Materially changes the experiment. A
  weaker answerer finds fewer conventions unaided, which *widens* the gap for a
  reason unrelated to the skill, and breaks comparability with every prior run
  in this project. It would need saying in the result, loudly.

Sample size stays at five per arm either way. Changing it after seeing partial
data is the kind of adjustment pre-registration exists to prevent.
