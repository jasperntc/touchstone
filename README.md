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
| F004 | absent information | 15 | +53.3 vs +40 | **skill not proven** |
| F005 | leaks repaired, skill v2 | 15 | +100.0 vs +40 | **skill not proven** |

> **On this evidence, a skill that restates what is already in the codebase
> does not beat no skill.**

F004 changed the question. It was the first run where a *skill* was evaluated at
all — F001–F003 rejected **tasks**, because the oracle barely beat the control
and no skill could have helped. Given information the codebase genuinely cannot
contain, the skill delivered **100% of what the raw facts delivered**.

Then it failed on a gate nothing else has. Scored against an unrelated task it
was never meant to touch, the skill made that task **worse** — 88.3% without it,
75.0% with it — and the effect was dose-dependent: on one convention, 3 of 5
controls applied it, 2 of 5 given the bare facts, and **0 of 5** given the skill.

The mechanism is in the answers' own words. The skill argues, vividly, that data
can be lost without anyone noticing. Every sample carrying it then refused to
truncate a list in a different package, explaining that truncating would
"silently drop" rows — the skill's own vocabulary, applied to a convention it
never mentions.

> **A skill is not only its content. It is a standing bias on everything the
> model does while it is loaded**, and the more vividly it argues its case, the
> further that bias reaches.

F005 repaired two leaks in that fixture — the control now scores **0% on all
three** withheld facts, against 40–100% before — and rewrote the skill in flat,
explicitly scoped prose. The skill delivered **100%**, the vivid-prose harm
disappeared entirely, and the run still failed the harm gate at −8.3, because
the *fix* caused a different one.

The skill now ends with a scope paragraph disclaiming any view on pagination
and ordering, and telling the reader to follow the codebase's own conventions.
On the unrelated task, `ids.valid` usage fell from 5/5 to **1/5** and sorting
from 5/5 to **3/5** — because "follow the codebase's conventions" points at the
majority pattern rather than the invariant the codebase states about itself,
and naming a topic to disclaim it puts the topic in play.

> **A scope disclaimer is not neutral.** Two skill versions, opposite prose
> styles, opposite failure modes, both outside tolerance.

That is why `skills/` is still empty, and why the gate that caught it — which
no other skill-evaluation framework has — is the part of this repository worth
keeping.

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

## If `skills/` is empty, what gets recommended?

Other people's work, and that was always the design. `skills/` is the shelf for
skills **this repository has proven**; it is not the catalogue. The catalogue is
the 31 skills in the official plugin marketplace, the built-in Anthropic skills,
and whatever `SearchSkills` finds in an org catalogue. A recommender does not
need to own a skill to point at one.

Recommending is already solved upstream — `claude-automation-recommender` in the
`claude-code-setup` plugin scans a codebase and suggests skills, plugins, hooks,
subagents and MCP servers, and the harness ships `SearchSkills` /
`SuggestSkills` / `SearchPlugins` / `SuggestPluginInstall`. Three things are not
solved, and they are what `tools/catalogue.py` adds:

- **No recommendation anywhere carries evidence.** "Recommended: X" reads the
  same whether X beat a control, was never measured, or was measured and found
  to do nothing. This is the only place those measurements exist.
- **The upstream lists are hand-maintained markdown** and go stale silently.
  This scans what is actually installed.
- **Negative results have nowhere to live.** 116 blind subagents found no effect
  from the 270 agency-agents bodies; without a field for that, the next person
  rediscovers it.

| label | means |
|---|---|
| `proven-here` | beat a control in a blind run, `RESULT.md` names it. **Currently: 0** |
| `shipped-unmeasured` | widely used, not measured here. **Currently: 31** |
| `measured-no-effect` | measured here, no effect found |
| `unproven` | everything else, and the default |

A label says who measured what against which control. It is not a ranking, and
`shipped-unmeasured` is the honest label for most good software.

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

**The evaluation itself is [skill-creator]'s job, not this repository's.** It
already spawns with-skill and baseline runs together, grades them, aggregates
mean/stddev/delta, judges A against B blind without being told which is which,
and tunes descriptions against a held-out split. A parallel harness here was
rebuilding that, and has been deleted.

What remains here is the three gates skill-creator does not have — an `oracle`
upper control, a threshold committed to git before the run, and a floor on how
many expectations carry the effect — plus per-run tree isolation for tasks about
a codebase. Each one corresponds to a false reading this project has already
produced. See **[docs/how-a-skill-gets-proven.md](docs/how-a-skill-gets-proven.md)**.

[skill-creator]: https://github.com/anthropics/claude-plugins-official

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

```bash
python eval/harness/prereg.py --register F004 --threshold 15
```

```bash
python eval/harness/prereg.py --verdict F004 --benchmark <workspace>/iteration-1/benchmark.json
```
