# How a skill gets proven

**skill-creator runs the evaluation. This repository supplies the gates it does
not have.** That split is new, and it replaced a parallel harness that had been
rebuilding machinery which already existed.

## What each side does

| | skill-creator | here |
|---|---|---|
| spawn with-skill and baseline runs together | ✅ | — |
| grade assertions, per run | ✅ | — |
| mean / stddev / min / max, delta between configs | ✅ | — |
| blind A/B comparator — *"you do NOT know which skill produced which"* | ✅ | — |
| flag assertions that always pass in both arms | ✅ (observed) | ✅ (**enforced**) |
| flag high-variance evals | ✅ | — |
| description tuning, 60/40 train/held-out split | ✅ | — |
| HTML review viewer | ✅ | — |
| **an `oracle` upper control** | — | ✅ |
| **a threshold committed before the run** | — | ✅ |
| **a floor on how many expectations carry the effect** | — | ✅ |
| **per-run tree isolation for codebase tasks** | — | ✅ |

Everything in the left column is better than what this repository had. It was
deleted rather than maintained alongside — see `blind_run.py` in the history if
you want to know what went.

## Why the three gates

Each corresponds to a false reading already produced here.

**The oracle arm.** skill-creator's baseline is `without_skill`, or the previous
version of the skill. Nothing hands over the answer outright, so a flat result
cannot distinguish *the skill adds nothing* from *nothing could have added
anything*. agency-agents scored 24/24 in every cell across 44 blind subagents
before that ambiguity was even visible. skill-creator's analyzer does flag an
expectation that always passes in both arms — but afterwards, as an
observation, not as a stop before the fleet is spent.

**The threshold, committed first.** skill-creator drafts assertions *while the
runs are in flight* (`SKILL.md:201`), which is correct for authoring and wrong
for deciding. F002 came in at +12.5. That reads as "promising, iterate" unless
+15 was already in git, in which case it reads as a fail — and it was a fail.

**The spread floor.** F002 and F003 both produced a pooled lift near +12 in
which a *single* expectation was the entire effect. A pooled average conceals
that completely. A collection of skills cannot be founded on one sortable list.

## The loop

**1. Register the bar, and commit it.**

```bash
python eval/harness/prereg.py --register F004 --threshold 15 --min-discriminating 2
```

`--verdict` reads the commit timestamp and refuses to score a run that started
first, so this commit has to land before anything is spawned.

**2. Stage one tree per run, if the task is about a codebase.**

```bash
python eval/harness/stage.py --fanout 6 --out ../_touchstone_staging
```

skill-creator gives each run its own *output* directory but not its own copy of
the thing being worked on. F001's third defect was one subagent's grep
surfacing a sibling's answer. Each tree here is also verified to sit outside
every git repository, because a control that can run `git show` is not a
control — that was F002's.

**3. Run skill-creator's eval, with a third arm.**

Follow its own workflow, and spawn `oracle` alongside `with_skill` and
`without_skill` — same prompt, with the information the skill would carry handed
over directly as text. Write it to `oracle/run-N/` beside the others.
`aggregate_benchmark.py` discovers configuration directories by listing rather
than by a hardcoded list (`aggregate_benchmark.py:100–107`), so the third arm is
picked up with no patch.

If the arms' prompts were assembled by hand, check them:

```bash
python eval/harness/prereg.py --check-prompts base.txt oracle.txt --treatment rules.txt
```

**4. Take the verdict.**

```bash
python eval/harness/prereg.py --verdict F004 --benchmark <workspace>/iteration-1/benchmark.json
```

It refuses on an unregistered or late-committed threshold, refuses on a missing
`oracle` arm, rejects the **task** if the oracle cannot beat the baseline, and
otherwise reports lift, spread, and what fraction of the oracle's proven
headroom the skill actually captured.

Only a `PROVEN` verdict earns a `RESULT.md`, which is what `skills/` requires.

## Two things to know about the seams

**A third config changes what skill-creator's own `delta` means.** It is
computed between `configs[0]` and `configs[1]` of a sorted listing
(`aggregate_benchmark.py:206`), so adding `oracle/` silently turns the headline
delta into `oracle − with_skill` rather than `with_skill − without_skill`. It is
not wrong — it is remaining headroom — but it is not what the label suggests.
Take the numbers from `--verdict`, which selects arms by name.

**skill-creator's layout tells a run which arm it is in.** Outputs go to
`with_skill/` and `without_skill/`, and the path is in the prompt. That is fine
for a capability skill and worth thinking about for anything where knowing you
are the control could change behaviour. The blind comparator is unaffected — it
judges outputs after the fact, without labels.

## Installing skill-creator

```bash
/plugin marketplace add anthropics/claude-plugins-official
```
