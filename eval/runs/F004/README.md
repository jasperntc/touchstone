# F004 — how to run it

Thresholds are in `eval/prereg/F004.json`, committed at `dd91d9b`, before the
fixture existed. `prereg.py --verdict` refuses to score a benchmark older than
that commit.

The design, and what each outcome means, is in
[docs/design-F004.md](../../../docs/design-F004.md).

## 1. Stage one tree per sample

```bash
python eval/harness/stage.py --fanout 15 --out ../_touchstone_staging
```

Fifteen trees: five per arm. Each is verified to sit outside every git
repository before it is handed out.

## 2. Spawn

Three arms, five samples each. The prompts in `prompts/` are rendered and
already checked — each treated arm differs from `without_skill.txt` by its
treatment block and nothing else:

```bash
python eval/harness/prereg.py --check-prompts \
  eval/runs/F004/prompts/without_skill.txt \
  eval/runs/F004/prompts/with_skill.txt \
  --treatment eval/runs/F004/prompts/_treatment_skill.txt
```

Substitute the real staged path for `CODE` in each prompt. Assign codes to arms
opaquely — nothing in a sample's own path should tell it which arm it is in.

Each answer goes to `<tree>/meridian/compliance/reverify.py`. Every sample also
answers `t002` at `<tree>/meridian/accounts/adjustments.py`, which is the harm
eval: the Certis skill has no business changing it.

## 3. Score

```bash
python eval/harness/to_benchmark.py --staging ../_touchstone_staging \
  --assign assign.json --out eval/runs/F004/benchmark.json
```

`assign.json` maps each staged directory name to `without_skill`, `oracle` or
`with_skill`. Read the SANITY FLOOR summary before anything else — a sample
that fails a functional check makes the run unreadable, not informative.

## 4. Verdict

```bash
python eval/harness/prereg.py --verdict F004 --benchmark eval/runs/F004/benchmark.json
```

Then read every SOURCES section by hand before believing it. F002's blindness
breach surfaced only because one subagent volunteered what it had done.

## What is deliberately not here

No `benchmark.json`. The loop was dry-run end to end with the calibration
drafts standing in for answers, and it returned PROVEN — which is worth knowing
about the instrument and worth nothing about the skill. That artifact was
deleted rather than committed, because a `PROVEN` benchmark sitting in a run
directory is exactly the thing that gets misread six weeks later.

## The run as executed

**2026-08-22. Fifteen `claude-opus-5` subagents, five per arm.** Same tier as
F001–F003, so a change in the result is a change in the fixture rather than in
the answerer.

Each sample does **two** tasks in one session, `t002` first and `t004` second.
That order is deliberate: `t002` is the harm eval, and asking it after the
Certis task would measure a model freshly primed on Certis rather than a model
that merely has the skill installed. Installed-then-unrelated-work is the real
situation being tested.

Arm assignment is in `assign.json`, committed before any subagent was spawned.
Codes are opaque and nothing in a sample's own path names its arm.
