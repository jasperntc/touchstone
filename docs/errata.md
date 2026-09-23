# Errata

Corrections to the record, found after the fact. `docs/findings.md` and
everything under `eval/` are left exactly as committed; corrections live here
instead, so the original text stays checkable.

All three entries are reproduced offline by

    python tools/verify.py --require-git

which re-scores every committed answer, regenerates the benchmarks and floors,
and checks the claims in `findings.md` against them. Times below are each
commit's own `%ci`.

No entry changes a reported number or gate verdict. E3 changes how far the
results can be relied on: under the harness's own rule F004 is unreadable, so
the conclusion rests on F005 alone.

---

## E1 — the task-validity gate is enforced at > 0, not at +40

**The record says.** Task validity requires `oracle − without_skill` ≥ **+40**
on the absent checks (`docs/design-F004.md:143`; `eval/prereg/F004.json:14`,
"Task validity gate is the +40"). The F004 and F005 gate tables report
"task validity | ≥ +40 | … | ok" (`findings.md:349`, `findings.md:478`).

**What is true.** `prereg.evaluate()` rejects a task only when headroom ≤ 0
(`eval/harness/prereg.py:185`). Any positive headroom passes, and
`ceiling_ok` is then set to `True` unconditionally (`prereg.py:218`). The
registration has no task-validity field; `primary_threshold_points` (40.0) is
the lift bar. The +40 was registered but never checked by the instrument.

**Evidence.** `eval/harness/prereg.py:185`, `:218`; `docs/design-F004.md:143`;
`eval/prereg/F004.json:3`, `:14`.

**Effect on reported results.** None. Measured headroom is +53.3 for F004 and
+73.3 for F005, both ≥ +40, so both "ok" entries are correct and both verdicts
stand. `tools/verify.py` checks headroom against the +40 bar independently of
`prereg.py`, so the published verification enforces the bar the gate did not.
The harness is left unchanged: fixing it would change the instrument that
produced the record.

---

## E2 — the design line was committed at `dd91d9b`, not `6322933`

**The record says.** `findings.md:573–575`: the design line
(`design-F004.md:143`) and the adapter's docstring were "Both … committed at
`6322933`, 03:15; t005 landed at `5f583a0`, 13:56, ten hours later."

**What is true.** The adapter docstring was committed at `6322933`
(2026-08-22 03:15:20 +0800), and "ten hours later" is correct for it. The design
line was committed earlier, at `dd91d9b` (2026-08-22 02:36:50 +0800), and is
unchanged since. It is present at `6322933`, but was not committed there. Its
gap to `5f583a0` (13:56:44) is about 11h20m.

**Evidence.** `git blame -L 143,143 docs/design-F004.md` → `dd91d9b`;
`git show dd91d9b:docs/design-F004.md` contains the line;
`git show 6322933:eval/harness/to_benchmark.py`, docstring lines 20–21.

**Effect on reported results.** None. The argument at that point in
`findings.md` is that the pre-registration predates the bug. That holds, and
the earlier commit only lengthens the margin. The F005 correction (+33.3 → +100
absent lift) stands as reported.

---

## E3 — F004 does not report that 3 of 5 controls failed the sanity floor

**The record says.** The F004 section of `findings.md` does not mention the
sanity floor. F005's one floor failure is reported (`findings.md:519–521`).

**What is true.** In `eval/runs/F004/floor.json`, three of the five
`without_skill` samples (`h2n`, `q4t`, `x8v`) fail the functional check
`f_a_clean_holder_is_clear`. In each, 20 holders that Certis answered with no
adverse findings were not reported clear. Every `oracle` and `with_skill`
sample passes. The harness's own guidance, committed at `6322933` and
unchanged at `2da2279`:

- `eval/harness/to_benchmark.py:31–32` (docstring): "a control that cannot do
  the job at all makes the run unreadable rather than informative."
- `eval/harness/to_benchmark.py:138–140` (printed under SANITY FLOOR): "Read
  those answers before trusting any number above them -- a control that fails
  the floor makes the run unreadable rather than informative."
- `eval/runs/F004/README.md:47–48`: "a sample that fails a functional check
  makes the run unreadable, not informative."

**Evidence.** `eval/runs/F004/floor.json` (committed in `2da2279`);
`tools/verify.py` regenerates it byte-identical and prints the three failures
under SANITY FLOOR in `build/verify/F004/to_benchmark.log`.

**Effect on reported results.** No number or verdict changes. The floor is not
an input to `prereg.evaluate()`, and F004's gate verdict remains NOT PROVEN.

The floor rule was committed at 6322933 (03:15), before F004 was
staged at 8a0d233 (03:31) and run, and three of F004's five controls
failed that floor. Two of the rule's three written forms plainly
cover this; only the docstring's narrower wording is arguable. Under
that rule F004 is unreadable, so its numbers, including the +53.3
headroom and lift in findings.md, shouldn't be cited as evidence.
That corrects findings.md:585–586, which says two runs agree: the
conclusion rests on F005 alone. F005's only floor failure was an
oracle sample, which the rule's control-specific wording doesn't
cover; the broader "a sample" wording appears only in F004's README.
F005's verdict, NOT PROVEN, is unchanged, so under the outcome rule
decided in advance for F004 (design-F004.md:163–164) its skill doesn't
ship either. F005's registration keeps F004's bars
(eval/prereg/F005.json:14) but doesn't restate that rule, so this
applies it by extension. I reported F004 without applying this rule.
