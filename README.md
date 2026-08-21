# Touchstone

*A collection of skills, none of which is here on anybody's say-so.*

A touchstone is the dark stone a jeweller rubs gold against: the streak
it leaves tells you the purity, whatever the piece looks like. The stone
is the instrument, not the inventory — which is the right way round for
this repository, where the measuring apparatus is the part that has
earned its keep so far.

Every entry in `skills/` carries a `RESULT.md` naming a blind run in which it
beat a control. A directory without one fails CI. "Proven" is a property of the
tree, not a claim in a readme.

This is a successor to `agency-agents`, which built 270 agent files and then
measured them: **116 blind subagents across two model tiers found no effect.**
That result is the reason this repository starts with **zero skills** and keeps
the instruments instead. See [docs/findings.md](docs/findings.md).

## The rule that shapes everything

> Calibrate the instrument before trusting a null from it.

Every task carries three conditions:

| condition | what it gets | role |
|---|---|---|
| `none` | the task and the codebase | lower control |
| `oracle` | the task, the codebase, and the answer's information handed over | **upper control** |
| `skill` | the task, the codebase, the skill under test | the thing being measured |

**If `oracle` does not beat `none`, the task is rejected — before any skill is
written.** The predecessor had two lower controls and no upper one, so three
task designs and 44 blind subagents went into a ceiling before anyone could
tell "the skill adds nothing" from "nothing could have added anything."

The first fixture built here failed that rule on day one, in six subagents.
Working as intended.

## What three fixtures measured

Twenty-two blind subagents across three fixtures, each with its threshold
committed to git before the run. None cleared it.

| | fixture | subagents | oracle lift | verdict |
|---|---|---:|---:|---|
| F001 | 6 files | 6 | **-26.7** | rejected |
| F002 | 52 files, 8 conventions | 6 | +12.5 vs +15 | rejected |
| F003 | 54 files, 10 conventions | 10 | +12.0 vs +15 | rejected |

> **On this evidence, a skill that restates what is already in the codebase
> does not beat no skill.**

In F003 the control scored 88% on ten house conventions it was told nothing
about, including two demonstrated in 5 of 27 modules. The single rule it
declined was the one that contradicted its instructions — and four of five
controls named that rule explicitly and gave reasons for rejecting it. They did
not fail to find it. They found it and judged against it.

The largest single difference between F002, whose controls missed the ordering
rule, and F003, whose controls got it five times out of five, is one sentence
added to the task: *"anything this brief does not pin down, match to the rest
of the codebase."* **One line of prompt did most of what a conventions skill
was supposed to do.**

So the premise changes, as [prediction-F003.md](docs/prediction-F003.md)
committed it would: to **information genuinely absent from the codebase** —
an incident that produced a rule, a decision taken in conversation, an
operational limit in a runbook, a contract with a repository the model cannot
see. Same instruments, different hypothesis.

What survives from three rejected fixtures is the apparatus. It now catches a
fixture reachable by `git show`, a fixture whose docstrings state their own
answers, a task its naive draft passes, a task whose middle draft fails the
wrong set, and a lift that is one convention wearing a pooled average as a
disguise. Each was found the expensive way first.

Full write-up: [docs/findings.md](docs/findings.md).

## Layout

    skills/       proven only: SKILL.md + eval/ + RESULT.md
    candidates/   unproven — drafts, imports, quarry extracts
    quarry/       the 270 predecessors, reference material, never shipped
    eval/
      fixture/    codebases with private conventions
      tasks/      questions; key/ is withheld while answers are collected
      harness/    the instruments
      runs/       recorded answers
    docs/findings.md

## How anything gets in

Source is irrelevant — my draft, your import, or a quarry extract all face the
same four gates:

1. security review
2. it ships its own eval (the eval is the admission ticket, not an afterthought)
3. the eval is calibrated: `oracle` must beat `none`
4. a blind run beats the control, recorded in `RESULT.md`

## Commands

```bash
python eval/harness/run_checks.py --self-test
```

```bash
python eval/harness/run_checks.py --calibrate
```

```bash
python eval/harness/run_checks.py --drafts
```

```bash
python eval/harness/stage.py --audit
```
