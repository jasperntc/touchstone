# What has been measured here

One entry so far, and it is a failure. That is the intended shape: this
repository's rule is that an instrument is calibrated before it is trusted, so
the first thing it produced is a rejected fixture rather than an accepted skill.

---

## F001 — the Meridian fixture does not discriminate. Rejected.

**2026-08-21. Six blind `claude-opus-5` subagents, three per condition.**

The fixture is a small internal codebase with six arbitrary house conventions —
money in micros, `(ok, value, error)` triples, error codes never prose, never
raise, `@audited` + `__all__`, injected clock. Every one is *demonstrated* in
the committed code and *stated* nowhere the answerer could read.

The premise: a model trained on the internet already knows good practice, which
is why the predecessor project's evaluations all ceilinged. It cannot know
*this* codebase's arbitrary choices, so a control has somewhere to lose.

| condition | functional | conventional |
|---|---:|---:|
| `none` — the task and the codebase | 6/6 | **15/15 (100%)** |
| `oracle` — the task, the codebase, and the six rules verbatim | 5/6 | 11/15 (73.3%) |

**Oracle lift: −26.7 points. The calibration fails.**

`none` followed all six arbitrary conventions, perfectly, three times out of
three, having been told none of them. Reading four small sibling modules was
enough. Handing the rules over made one answer *worse*: given rule 6 as an
imperative — *"take a `clock` argument"* — it added a clock and returned a dict
where the rest of the codebase would not have, a literal reading the fixture's
own code does not support.

Under this repository's rule the **task is rejected, not the answers.** A
fixture where the upper control loses to the lower control cannot measure a
skill in between.

### Three defects in the instrument, all found in this one run

1. **The key guessed function names.** `check_c_is_audited_and_exported` and the
   `_fn` helper looked for `available_balance*`. A `none` answer that obeyed
   every rule but called itself `available_micros` scored **0/5**, which read as
   a model failing to infer conventions and was entirely a defect here. Graded
   against `__all__` now. *The uncorrected numbers would have told the opposite
   story: `none` 66.7% against `oracle` 73.3%, a tidy positive lift that was
   pure grader artefact.*
2. **The task was already implemented.** `ledger.total_posted_micros` does
   exactly what the brief asks, so five of six answers delegated to it and
   inherited its conventions for free. Independently flagged by four subagents.
3. **Samples were not independent.** Runs wrote into a shared visible tree; one
   subagent's grep surfaced a sibling's answer, and another saw two more appear
   mid-run. Output must be isolated per sample.

### What this says, and the part to be careful about

The premise behind this whole repository was that **private project context is
something a model cannot have**. That is false in the case tested: when the
convention is visible in code the model can read, it infers it reliably.

Two explanations survive, and they are not equally comfortable:

- **The effect is not there.** Frontier models read a codebase and match its
  style, and a skill restating that style adds nothing — the same shape of
  result as the predecessor's 116 blind subagents.
- **The fixture was too small.** Six files, trivially read end to end. A real
  codebase cannot be read exhaustively, and a skill that names the rules might
  save a model from sampling the wrong corner of it.

The second is testable and cheap. It is also the fourth time across two
repositories that a null has been met with *"the task was too easy"* — after
c001–c006, after the Sonnet arm, after c007, and now here. **Each rescue is
individually reasonable and the pattern is not.** If a scaled-up fixture also
shows no gap, the honest conclusion is that the effect does not exist at this
granularity, and the answer to "do skills beat no skills" is no.

That test is worth running once, with the result written down in advance, and
it is the last rescue this hypothesis gets.
