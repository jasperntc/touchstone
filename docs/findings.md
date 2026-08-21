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

---

## F002 — breadth produces a real but sub-threshold gap. Fixture rejected.

**2026-08-21. Six blind `claude-opus-5` subagents, three per condition.**
Threshold fixed in [prediction-F002.md](prediction-F002.md) before the run.

The fixture grew to 36 modules across 11 packages, 52 files, 1,372 lines. Five
conventions wide, three narrow — injected clock, id-shape validation,
newest-first ordering — and none of the three demonstrated in `accounts/`,
where the task lives.

| arm | functional | conventional | missed |
|---|---:|---:|---|
| `none` q4m | 2/2 | 8/8 | — **contaminated, see below** |
| `none` n8x | 2/2 | 7/8 | c8 ordering |
| `none` v2p | 2/2 | 7/8 | c8 ordering |
| `oracle` ×3 | 6/6 | **24/24 (100%)** | — |

| comparison | lift |
|---|---:|
| oracle vs the two clean controls | **+12.5** |
| oracle vs all three | +8.3 |
| **pre-registered threshold** | **+15.0** |

**Below threshold. The fixture is rejected**, per the rule written down before
the run: a lift between 0 and +15 is too small to build on at one sample per
cell, and moving the bar after seeing +12.5 is the thing pre-registration
exists to prevent.

### What the gap actually consists of

One convention. Both clean controls found the clock (C6) and id-shape
validation (C7) despite neither being demonstrated anywhere in the package they
were working in — they read widely, and one explicitly reported that the
neighbouring `accounts/` files were *"the wrong template"* because they validate
by truthiness. What both missed was **ordering**, and only ordering.

So breadth is not nothing, and it is much less than F001's −26.7 suggested. But
"the entire measured effect is one convention out of eight, in two samples" is
not a foundation to build a skill collection on.

### The blindness breach, which is mine

`none` q4m scored 8/8 because it **retrieved `CONVENTIONS.md` from the
repository's git history**. It said so unprompted. I had moved the file out of
the working tree and then committed it, in the same session, at `7fd2183` — so
`git show` handed over all eight rules.

Stashing the working tree is not blindness when the answer key is in the object
store. Every prior run in both repositories used the same procedure, so the
same hole existed and simply was not exercised. The fix is structural: serve
the fixture from a directory with **no git history**, rather than from a
subdirectory of the repository that holds the key.

Counting q4m as a control drags the lift down to +8.3; excluding it gives
+12.5. Both fail. The result does not turn on the breach, but the procedure
does not survive it.

### Five instrument defects, four caught before the run

Caught pre-flight, by building the calibration first:

1. **`c8` could not fail** — the store listed `acc_101` already newest-first, so
   an answer that never sorted passed for free. Given the outcome above, this
   one mattered: c8 is the entire measured effect, and uncaught it would have
   erased the gap completely and produced a false null.
2. **C6 was entangled with correctness** — rows anchored to a fixed past instant
   made every wall-time answer functionally wrong.
3. **Module docstrings recited the conventions** — one grep for "convention"
   would have handed a control all eight.
4. **My own design commentary in `_store.py`** stated c8's expected answer
   outright, in the one file the brief tells the answerer to read.

Caught only by a subagent volunteering it:

5. **git history**, above.

### Standing

The hypothesis is not dead — the pre-registered meaning of "≤ 0" was not met,
and the direction is right. But it has now consumed two fixtures and twelve
blind subagents without clearing a bar set in advance, and this was already the
last rescue. **The next attempt must be the last, and it must be pre-registered
the same way.** If a fixture with no-git isolation and more than one
discriminating convention still lands under +15, the collection's premise
changes to information genuinely absent from the codebase, or it stops.

---

## F003 — the control found nine of the ten conventions. Both thresholds missed. Premise rejected.

**2026-08-21. Ten blind `claude-opus-5` subagents, five per condition.** Both
thresholds fixed in [prediction-F003.md](prediction-F003.md) before the run.

| arm | functional | conventional |
|---|---:|---:|
| `none` — the task and the codebase | 10/10 (100%) | **44/50 (88.0%)** |
| `oracle` — the same, plus the ten rules | 10/10 (100%) | **50/50 (100%)** |

| threshold | required | measured | |
|---|---|---:|---|
| primary — pooled conventional lift | ≥ +15.0 | **+12.0** | MISSED |
| secondary — conventions with a gap ≥ 40 | ≥ 2 | **1** | MISSED |

**Rejected on both.** F002 was +12.5 and F003 is +12.0: two fixtures, three new conventions, a
larger sample and a closed blindness hole, and essentially the same number.

### Where the gap is, and it is one place

| check | `none` | `oracle` | gap |
|---|---:|---:|---:|
| c1 micros · c2 triple · c3 codes · c4 no-raise · c5 audited | 100% | 100% | +0 |
| c6 injected clock | 100% | 100% | **+0** |
| c7 id shape | 80% | 100% | +20 |
| c8 newest first | 100% | 100% | **+0** |
| c9 capped at PAGE_LIMIT | 100% | 100% | **+0** |
| c10 zero rows not listed | **0%** | **100%** | **+100** |

Five of five oracles filtered zero-amount rows. Zero of five controls did. A
clean split — and the only one on the board.

C8 and C9 were the two conventions this fixture was rebuilt around, chosen as
the "invisible" kind that F002's controls had missed. **Every control got both,
five times out of five.** The legibility theory the fixture was designed on is
wrong, or at least it was not what F002 was measuring.

### The control did not fail to find C10. It found it and decided against it.

Four of the five controls raised the zero-amount filter unprompted and gave
reasons for rejecting it:

> "the brief names only two exclusions and that filter is an undocumented
> 3-of-26 minority" — `k7r`

> "I deliberately did *not* filter the zero-amount `adj_32` row even though
> several modules filter `amount_micros != 0`, because the brief named window
> and account as the only exclusions" — `m2v`

> "I deliberately did not copy the minority `amount_micros != 0` filter" — `b4x`

That is not a discovery gap. Both arms knew the pattern existed; the arms
differ in whether a rule was **asserted with authority**. What the oracle
supplied was not information, it was standing — permission to override both the
brief and the majority of the code.

That may well be a real thing skills do. It is not the thing this repository
set out to measure, and it is not "the skill saved you a search."

### Three defects, all found by reading what the controls wrote

**1. Four of the ten conventions were stated outright in module docstrings.**

| file | docstring | states |
|---|---|---|
| `errors.py` | "Every failure in current Meridian code is one of these." | C3 |
| `audit.py` | "Every current export wears one." | C5 |
| `ids.py` | "Every current entry point validates through here." | C7 |
| `clock.py` | "The only source of time in current Meridian code." | C6 |

The controls quoted them back verbatim as justification — one followed
`ids.valid` against a 22-of-25 local majority because "`ids.py` states it as the
entry-point invariant". `--audit` existed precisely to catch this and reported
the fixture **clean**, because its flag list was substrings of normative words
— *always, never, must, convention* — and not one of these four contains one.
They are universal-quantifier **declaratives**, a grammatical form the detector
could not see at all. The substring list misses 4 of 4; the regexes that
replaced it catch 4 of 4.

These five docstrings are written by `main()` in the generator, so the
"neutral prose only" fix applied to `current_module` after F002 never reached
them. **The fixture has not been edited to remove them.** Retroactively
changing the thing an experiment ran on is worse than recording what it was.

**2. C8, C9 and C10 are not narrow conventions. They are minority patterns the
majority of current code contradicts.** Of 27 current modules returning a row
list, 5 sort, 5 cap and 3 filter zeros — so 22 return unsorted lists. "Narrow"
was supposed to mean *demonstrated in few places*; it actually meant
*contradicted in most places*. The brief tells both arms to match the codebase,
and for these three the codebase's majority says don't. One oracle put it
plainly: *"No existing module follows all ten conventions at once — the
codebase is a mosaic where each file honors a subset."* A real codebase's
conventions are the majority pattern in current code. This fixture inverted
that, which flatters the oracle for a reason unrelated to skills.

**3. C10 contradicts the brief.** The brief asks for the account's rows in the
window; C10 removes some of them. Softening the wording — "are never included",
"nothing to report" — was not enough, and three controls cited the brief by
name when declining. **The single convention that discriminated is the single
one that conflicts with the task description.** An instruction conflict is not a
conventions gap.

### The pre-registered failure mode that fired

Written before the run, as the second of three ways this could fail:

> The brief's new closing sentence does most of the work, and a control that
> goes looking for conventions because it was told to finds all of them. That
> would be a real and useful finding about prompts rather than skills.

F002's controls missed ordering. F003's got it five times out of five. The
fixture grew and the conventions changed, but the largest single difference
between the two runs is one sentence added to the brief: *"Anything this brief
does not pin down, match to the rest of the codebase."*

**On this evidence, one sentence of prompt does most of what a conventions
skill was supposed to do.** That is not a null result. It is a cheaper
mechanism for the same outcome, and it is the most useful thing either fixture
has produced.

### Blindness, this time

Held. The isolation fix worked and was independently confirmed: several
subagents ran `git status` inside their tree and reported back that it was not
a repository. Every one of the ten SOURCES sections disclaimed the internet,
other directories, version control and recollection of a similar codebase. All
ten staged trees were hash-verified against the fixture afterwards: 54 files
each, byte-identical, the answer file the only addition.

Requiring disclosure rather than hoping for it is the change that made this
checkable. F002's breach surfaced because one subagent happened to volunteer
it.

### The decision, taken as written

Both thresholds missed, so by the rule fixed before the run the premise is
**rejected, not rescued**. Three fixtures, twenty-two blind subagents, and no
run has cleared a bar set in advance.

> **On this evidence, a skill that restates what is already in the codebase does
> not beat no skill.** A frontier model reading the tree finds the conventions,
> including ones demonstrated in 5 of 27 modules, and the only rule it will not
> adopt unaided is one that contradicts its instructions.

What this does not rule out, and what the collection's premise becomes:
**information genuinely absent from the codebase.** An incident that produced a
rule, a decision taken in a conversation, an operational limit that lives in a
runbook, a contract with a repository the model cannot see. That is a different
hypothesis, it is testable with these same instruments, and the F003 result
points straight at it — the one convention the control refused was the one
nothing in the code could justify strongly enough to override the brief.

**What survives from three rejected fixtures is the apparatus**, which now
catches: a fixture reachable by `git show`, a fixture whose docstrings state
their own answers, a task whose naive draft passes, a task whose middle draft
fails the wrong set, and a lift that is really one convention wearing a pooled
average as a disguise. Every one of those was found the expensive way first.
