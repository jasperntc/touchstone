# Prediction for F003, written before the run

Committed before any subagent is spawned. The value of this file is entirely in
its timestamp: a threshold chosen after seeing the numbers is not a threshold.

This is the **last** test of the premise that a skill restating a codebase's own
conventions beats no skill. F002's writeup said so, F001's said so before it,
and saying it a third time is worth nothing unless the decision rule below is
followed whatever the number turns out to be — including if it lands at +14.

## What F002 left

+12.5 against a threshold of +15, and the whole of it was **one** convention.
Both clean controls found the injected clock and id-shape validation unaided;
both missed ordering, and only ordering.

The split that predicts which survived is not narrow-versus-wide. It is
**legibility**:

| | |
|---|---|
| found by controls | micros naming, return triples, error codes, no-raise, `@audited`, a `clock` parameter, an `ids.valid` call |
| missed by controls | ordering |

Everything in the first row is visible at a glance in any module that happens
to be open — in a signature, a return statement, a decorator line. Ordering is
visible only by reading what a function does to rows *after* it has them.

## What F003 changes

Two conventions from the second category, chosen to be structurally
independent of ordering and of each other:

    C8   rows come back newest first                    a sort
    C9   a listing returns at most PAGE_LIMIT rows,     a slice
         the cap applied after the sort
    C10  rows whose amount_micros is exactly 0          a filter
         are not listed

Graded on three different accounts — `acc_102`, `acc_101`, `acc_103` — so that
failing one does not mechanically fail the others. F002 could not distinguish
"the effect is small" from "the effect is one convention" because they were the
same number.

Both new conventions are demonstrated in committed code: the cap in 5 of 27
current modules, the filter in 3, neither anywhere in `accounts/`, where the
task lives. Nothing here is knowable only by being told. That would be a
different experiment and a much easier one, and it is the *next* premise, not
this one.

### The selection effect, stated rather than buried

C9 and C10 were chosen **because they resemble the one convention that produced
a gap in F002**. That makes a gap more likely and it makes this result weaker
than an unbiased design would be. Two things constrain it, both fixed here
before the run:

- The wide conventions stay in the fixture and in the denominator. The primary
  threshold is **+15 on the full ten-check conventional rate** — the same
  measure, on the same scale, that F002 was judged against. A contested-subset
  rate would be a friendlier bar and is reported below only as description.
- Every convention must be reachable by reading. `--drafts` enforces the
  placement half of that on every push: the partial draft must fail *exactly*
  the five narrow conventions, so a narrow one drifting into `accounts/` breaks
  CI instead of quietly changing the experiment.

### One further change, and its direction

The brief no longer implies exhaustiveness, and now ends *"anything this brief
does not pin down, match to the rest of the codebase."* Under C9 and C10 the
conventional answer returns **fewer** rows than the old wording demanded, so
without this a control would have been marked down for obeying the brief and
the gap would have been manufactured outright. Both arms get the sentence. It
helps the control, which is the conservative direction.

## The instrument, calibrated before the prediction

| draft | functional | conventional | fails |
|---|---:|---:|---|
| `reference` — knows all ten | 2/2 | **10/10** | — |
| `partial` — read `accounts/` and nothing else | 2/2 | **5/10** | C6, C7, C8, C9, C10 |
| `naive` — written in the legacy style | 2/2 | **0/10** | all ten |

Three separate levels, all clearing the functional floor. `partial` fails
exactly the narrow set, which is now a CI gate rather than an observation.

## Blindness

F002's `none/q4m` recovered `CONVENTIONS.md` with `git show` and said so. The
fixture is now staged by `eval/harness/stage.py` into a directory where no
`.git` resolves — not in the tree, not in any ancestor — and the conventions
are **never written to disk in any condition**; the oracle arm receives them in
its prompt. There is no file for any arm to find.

Every answerer is required to report what it read. F002's breach was caught
only because one subagent volunteered it, and luck is not a control.

## The prediction

Mapping F002's clean controls onto this fixture: they took C1–C7 and missed
C8. Here that is 7 of 10.

| | prediction |
|---|---|
| `none` conventional | **6–8 of 10** (60–80%), point estimate 70% |
| `oracle` conventional | **10 of 10** (100%) |
| primary lift | **+30**, and the threshold is +15 |
| contested C8/C9/C10 missed by `none` | 2 or 3 of 3 |

What would make this fail, in order of how much I expect it:

1. Controls read widely enough to find the cap and the filter too. The
   legibility theory is then wrong and (B) — there is no effect — is the honest
   reading.
2. The brief's new closing sentence does most of the work, and a control that
   goes looking for conventions because it was told to finds all of them. That
   would be a real and useful finding about prompts rather than skills.
3. The oracle misapplies a rule, as it did in F001, and loses ground it was
   handed.

## The thresholds, fixed now

**Both must hold for the fixture to be accepted.**

1. **Primary.** `oracle` − `none` ≥ **+15 points** on the full ten-check
   conventional rate, pooled across samples.
2. **Secondary, and equally binding.** At least **two** conventions must show a
   per-convention gap of **≥ 40 points** (`oracle` pass rate minus `none` pass
   rate for that check). With five samples an arm scores each check in fifths,
   so this means at least two conventions the controls get wrong more often
   than not.

The second exists because F002 cleared neither bar but came close to the first
while failing the second completely, and "one convention out of ten" can clear
+15 on arithmetic alone. A collection of skills cannot be founded on a single
sortable list.

## Analysis plan, also fixed now

- `functional` and `conventional` are never blended.
- A sample that fails to import scores 0 and is **reported, not dropped**.
- A sample that reports having reached the conventions by any route is excluded
  from the primary figure, and the figure is reported **both ways**, as F002
  did with q4m.
- The per-convention table is published in full, including the wide
  conventions, whatever it shows.

## What each outcome means, decided in advance

- **Both thresholds met.** The fixture measures. A `skill` arm is written
  against this same task and run as a third condition, and only a skill that
  beats `none` on it enters `skills/`.
- **Either threshold missed.** The premise is rejected. Not "rescued with a
  bigger fixture" — that has now been the response three times, and this file
  is the commitment not to make it a fourth. The collection's premise changes
  to **information genuinely absent from the codebase** — past incidents,
  decisions taken in conversation, operational limits, cross-repo contracts —
  which is a different and testable hypothesis, and the conclusion goes in the
  README: *on this evidence, a skill restating what is already in the codebase
  does not beat no skill.*

## Sample size, stated as the limit it is

**Five per condition, ten subagents, 50 conventional checks per arm** — up from
three and 24 in F002, where a single contaminated sample moved the headline
figure by four points. It detects a large effect and nothing subtle. A lift of
+15 or more is visible at this size; anything smaller is not something this run
can honestly claim in either direction.

One task, not two. That is a real limit and it is deliberate: two tasks would
double the surface for the kind of instrument defect that has produced four
false readings across two repositories. Whatever this measures, it measures
about `recent_adjustments` in `accounts/`, and a second task would be the first
thing to run if the fixture is accepted.

## The model, recorded before spawning

**`claude-opus-5`**, the same tier F001 and F002 used. The prediction above --
`none` at 60-80% -- is read straight off F002's Opus controls, so running a
different tier would leave no way to tell a change in the fixture from a change
in the answerer. A weaker control finding fewer conventions would widen the gap
for a reason that has nothing to do with what is being tested.
