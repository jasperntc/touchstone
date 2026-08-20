# assay

*A collection of skills, none of which is here on anybody's say-so.*

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
