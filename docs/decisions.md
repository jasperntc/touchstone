# Decisions

Why the experiment is built the way it is, and what each choice can't tell you.
Unpathed scripts live in `eval/harness/`, `.md` files in `docs/`.

## Three arms, one of them an oracle

Every run needs `without_skill`, `oracle` and `with_skill` (`prereg.py:65`,
`eval/prereg/F005.json:6-10`). The oracle gets the facts in its prompt
(`eval/runs/F005/prompts/oracle.txt:10-24`).

**Why:** without it, a null can't separate "the skill adds nothing" from
"nothing could have added anything" (`prereg.py:22-31`).

**What it can't tell you:** the oracle is my wording. Four of five F005 oracle
samples read "again" as "twice in one pass" (`findings.md:508-511`), so
headroom measures my wording too (`findings.md:514-517`).

## Task validity

I registered +40 on the absent checks (`design-F004.md:143`,
`eval/prereg/F004.json:14`). The code rejects a task only at headroom ≤ 0
(`prereg.py:185`). That gap is E1 (`errata.md:21-32`).

**Why:** no skill beats a ceiling (`prereg.py:30-31`).

**What it can't tell you:** "ok" in the gate tables meant "> 0" to `prereg.py`.
F005 cleared it at +73.3 (`findings.md:478`); `tools/verify.py` checks that
bar, `prereg.py` doesn't (`errata.md:39-40`). And since capture can
exceed 100% (`prereg.py:194`), lift ≥ +40 doesn't imply headroom ≥ +40.

## The lift bar

`with_skill − without_skill` must reach +40 (`eval/prereg/F005.json:3`,
`prereg.py:192`) on absent checks only (`to_benchmark.py:20-22`).

**Why:** I picked +40 as a large, unmistakable effect; it isn't derived from a
power calculation.

**What it can't tell you:** with absent information the oracle wins by
construction, so lift alone mostly shows the facts help (`prereg.py:196-200`).
F005's +100 is three checks, 0/15 to 15/15 (`findings.md:470-474`).

## The spread gate

At least 2 expectations must show a gap ≥ 40 points (`eval/prereg/F005.json:4-5`,
`prereg.py:182-183`, `:193`).

**Why:** F002 and F003 each had a pooled lift near +12 that one expectation
carried (`prereg.py:40-43`).

**What it can't tell you:** at five samples, 40 points is two samples
(`prereg.py:177-180`). With three absent checks (`design-F004.md:145`), two is
most of them.

## Capture, and why it can exceed 100%

Capture is lift ÷ headroom (`prereg.py:194`); the bar is 70%
(`eval/prereg/F005.json:11`).

**Why:** what matters is how much of the oracle's headroom the packaged skill
delivers (`prereg.py:196-200`).

**What it can't tell you:** F005's 136% is +100 ÷ +73.3 (`findings.md:478-481`).
Four oracle samples memoised or capped the call; the skill said "Filter them out
before calling" (`findings.md:509-512`). Above 100% measures my oracle wording,
not packaging beating facts (`findings.md:507-517`).

## The harm check: one-sided, −5

`t002` is held out; with runs, it fails only if `with_skill` falls more than 5
points below `without_skill` (`prereg.py:204-209`, `eval/prereg/F005.json:12-13`).
A declared harm eval with no runs fails (`prereg.py:210-211`).

**Why:** pooling an unrelated task in would let damage hide inside a good
average (`prereg.py:149-155`).

**What it can't tell you:** it's one unrelated task, and −5 is three of its 60
checks per arm (`eval/runs/F005/benchmark.json:130`).

## Pre-registration in git

`--register` won't overwrite (`prereg.py:80-84`). `--verdict` won't score unless
the registration is tracked, matches HEAD and was committed before the benchmark
(`prereg.py:226-245`).

**Why:** F002 landed at +12.5 against +15 and was a failure only because the bar
was in git first (`prereg.py:35-37`).

**What it can't tell you:** "before" compares a commit time with a file's
modification time (`prereg.py:238-241`), both set on my machine. It fixed the
numbers but not which checks they cover (`to_benchmark.py:38-41`).

## What "blind" means here

No reachable git and no key in the staged tree (`stage.py:24-29`, `:114-146`); an
instruction to work only there (`eval/runs/F005/prompts/without_skill.txt:7-8`);
and a SOURCES section to audit by hand (`:30-33`,
`eval/runs/F004/README.md:56-57`).

**Why:** F002's control recovered the conventions with `git show`
(`findings.md:125-128`).

**What it can't tell you:** it's not a sandbox. Staging sits next to the repo
(`stage.py:61`), and `verify()` checks git and names, not access
(`stage.py:114-146`). Nothing blocks reading the repo. Subagents were
instructed and audited, not prevented. Inference: the key states all three
absent facts (`eval/tasks/key/t005.py:89-103`), yet F005's controls scored 0/15
on them (`findings.md:472`). That's hard to square with reading it, though not
proof.

## Deterministic keys

Answers are graded by code; for the Certis task, a fake client records what was
submitted (`eval/tasks/key/t005.py:109`, `to_benchmark.py:9-13`).

**Why:** these tasks have checkable right answers
(`eval/tasks/key/t002.py:44-102`, `eval/tasks/key/t005.py:62-104`), and code
scores them the same way every time (`tools/verify.py:13-17`).

**What it can't tell you:** deterministic isn't valid: a hardcoded `"t004"` once
flipped F005's verdict (`findings.md:564-570`).

## Five samples per arm

**Why:** I was limited by the cost of the API spend. F005 used 5
(`findings.md:465`).

**What it can't tell you:** F005's harm result supports only this: the
registered gate failed, −8.3 against −5 (`findings.md:482`). Per sample, the
control scored 10, 10, 11, 10, 10 of 12 and the skill 8, 10, 9, 11, 8
(`eval/runs/F005/benchmark.json:128-1371`). That's 5 checks of 60, the arms
overlap, and the gate runs no significance test (`prereg.py:204-209`). It can't
support "this skill reliably harms unrelated work".

## One codebase, one model

One synthetic codebase and `claude-opus-5` (`README.md:116`, `findings.md:333`,
`:465`).

**Why:** a fixed tier means a changed result reflects the fixture, not the
answerer (`eval/runs/F004/README.md:69-71`).

**What it can't tell you:** anything about other codebases, models, or
tool-bundling skills (`README.md:116-121`).

## NOT PROVEN by default

PROVEN needs lift, spread, capture and harm to pass (`prereg.py:213-216`); a
missing arm is UNREADABLE (`:144-147`).

**Why:** a skill enters `skills/` only if every gate is met
(`design-F004.md:153-155`, `:163-164`).

**What it can't tell you:** a control that ran only the harm eval reads as 0%,
and the verdict can be PROVEN (E4, `errata.md:121-128`). Neither run triggered
it (`errata.md:138-141`).

## The floor rule, and E3

Functional and conventional checks form a sanity floor, written to
`floor.json` and printed (`to_benchmark.py:31-34`, `:152-163`).

**Why:** a control that can't do the job makes the run unreadable
(`to_benchmark.py:32-34`).

**What it can't tell you:** the floor isn't an input to `evaluate()`
(`errata.md:93-94`), so it depends on me. Three of F004's five controls failed it
(`errata.md:74-79`), and I reported F004 anyway (`errata.md:110`). That's E3, my
decision. Under that rule F004 is unreadable, and the conclusion rests on F005
alone (`errata.md:15-17`).

## Publishing the answer keys

The keys are committed (`eval/tasks/key/`) and kept out of staging
(`stage.py:140-141`).

**Why:** anyone can re-score every committed answer (`errata.md:7-13`).

**What it can't tell you:** that no subagent read them. They sat in the repo
beside staging (`stage.py:61`). Publishing them also spends the
fixture as a blind test.

## Freezing the record; correcting via errata

`findings.md` and everything under `eval/` stay as committed; corrections go in
`errata.md` (`errata.md:3-5`); harness bugs stay unfixed.

**Why:** the original stays checkable, and the instrument stays the one that
produced the record (`errata.md:4-5`, `:41-42`).

**What it can't tell you:** whether a reader finds them. These are four
corrections to my own record; only E1 and E4 are harness bugs
(`errata.md:21-143`).

## What I'd do differently

- **Enforce in code what I wrote in prose.** The +40 validity bar and the floor
  were prose the gate ignored (E1, `prereg.py:185`; E3,
  `to_benchmark.py:152-163`, `errata.md:93-94`).
- **Write the gate tests before the runs.** E4 sat in `evaluate()` until a test
  exposed it (`errata.md:130-133`), and a hardcoded `"t004"` flipped a verdict
  (`findings.md:564-570`).
- **Commit a hash of the keys and release them after the run,** so they're
  checkable without sitting beside staging (`stage.py:61`).
- **Size n from the −5 tolerance.** F005's harm was 5 checks of 60, with
  overlapping samples (`eval/runs/F005/benchmark.json:128-1371`).
- **Add a placebo-skill arm.** Whether loading any skill costs something on
  unrelated work is open (`findings.md:591-595`); F004's evidence is unreadable
  under E3.
