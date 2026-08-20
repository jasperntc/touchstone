# Prediction for F002, written before the run

Committed before any subagent is spawned. The value of this file is entirely in
its timestamp: a threshold chosen after seeing the numbers is not a threshold.

## What is being tested

F001 failed: six small files, and the control inferred all six conventions, so
the oracle had nothing to add. Two explanations survived.

- **(A) Breadth.** The fixture was small enough to read end to end. In a real
  codebase a model reads a fraction, and a skill that names the conventions
  saves it from having to find them.
- **(B) There is no effect.** Frontier models match a codebase's style from
  whatever they read, and a skill restating it adds nothing.

F002 tests (A). The fixture is now **52 files, 1,372 lines, 36 modules across
11 packages**. Five conventions are **wide** (visible in most modules); three
are **narrow** — the injected clock (5 modules), id-shape validation (3), and
newest-first ordering (5). **None of the three narrow conventions appears in
`accounts/`, the package the task lives in.**

That placement is the mechanism, and it is a choice. It is realistic —
project-wide conventions are not re-demonstrated in every package — but if the
control reads widely enough to find them anyway, then (A) is not the
explanation and the result must be read as evidence for (B).

## The instrument, calibrated before the prediction

| draft | functional | conventional | fails |
|---|---:|---:|---|
| `reference` — knows all eight | 2/2 | **8/8** | — |
| `partial` — models a control that read only `accounts/` | 2/2 | **5/8** | c6, c7, c8 |
| `naive` — copied a legacy module | 2/2 | **0/8** | all |

All three clear the functional floor, and `partial` fails exactly the three
narrow conventions. The grader discriminates at three separate levels, so a
result between 5/8 and 8/8 is readable.

## The prediction

`none` is expected to land near `partial`: it should pick up the wide
conventions, because they are everywhere and it should, and miss some or all of
the narrow ones.

| | prediction |
|---|---|
| `none` conventional | **5–7 of 8** (62–88%) |
| `oracle` conventional | **8 of 8** (100%) |
| lift | **+15 points or more** |

## The threshold, fixed now

**Calibration PASSES if `oracle` − `none` ≥ +15 points on the conventional
rate.** Anything less and the fixture is rejected exactly as F001 was.

## What each outcome means, decided in advance

- **Lift ≥ +15.** (A) holds. Breadth is the mechanism, this fixture can measure
  a skill, and the first real skill gets written against it.
- **Lift between 0 and +15.** Too small to build on with one sample per cell.
  Treated as a fail; the fixture is not used.
- **Lift ≤ 0.** (B). This was the fourth "the task was too easy" across two
  repositories and it was declared the last one. The conclusion goes in the
  README: **on this evidence, a skill restating what is already in the
  codebase does not beat no skill**, and the collection's premise needs to
  change to information genuinely absent from the repo — past incidents,
  verbal decisions, operational limits — or be abandoned.

## Sample size, stated as the limit it is

Three per condition, 24 conventional checks per arm. That detects a large
effect and nothing subtle. A lift of +15 or more would be visible at this size;
anything smaller is not something this run can honestly claim either way.
