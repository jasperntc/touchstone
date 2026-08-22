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

---

## F004 — the skill delivered everything, and made unrelated work worse. Not proven.

**2026-08-22. Fifteen blind `claude-opus-5` subagents, five per arm.** Four gates
fixed in [design-F004.md](design-F004.md) and `eval/prereg/F004.json`, committed
before the fixture existed.

The first run in this project where a **skill** was evaluated at all. F001–F003
rejected *tasks* — the oracle barely beat the control, so no skill could have
helped and none was written.

| arm | t004 absent checks |
|---|---:|
| `without_skill` | 7/15 (46.7%) |
| `oracle` | **15/15 (100%)** |
| `with_skill` | **15/15 (100%)** |

| gate | bar | measured | |
|---|---|---:|---|
| task validity | ≥ +40 | **+53.3** | ok |
| lift | ≥ +40 | **+53.3** | MET |
| spread | ≥ 2 | **2** | MET |
| **capture** | ≥ 70% | **100%** | MET |
| **no harm** | ≥ −5 | **−13.3** | **REGRESSED** |

**NOT PROVEN.** Three gates cleared handsomely and the fourth failed, and the
fourth is the one no other skill-evaluation framework has.

### The skill worked

`with_skill` matched `oracle` exactly — 15/15 on the absent checks, five
samples, no variance. **The packaging delivered 100% of what the raw facts
delivered.** That was the gate this run existed to ask, F001 had shown it was
not automatic, and the answer is that a well-written skill loses nothing.

### And then it damaged the unrelated task

`t002` — recent-adjustments, nothing to do with identity verification — was held
out of the primary numbers and scored separately.

| | `without_skill` | `oracle` | `with_skill` |
|---|---:|---:|---:|
| t002 overall | **88.3%** | 83.3% | **75.0%** |
| c7 id-shape validation | 100% | 100% | 80% |
| c8 newest-first ordering | 100% | 60% | **20%** |
| c9 capped at PAGE_LIMIT | 60% | 40% | **0%** |

Not noise. Per-sample totals were 11,11,10,10,11 for the control against
9,10,9,9,8 with the skill — the distributions barely touch.

And it is **dose-dependent**. On applying the paging convention:

    without_skill   3 of 5 applied it
    oracle          2 of 5
    with_skill      0 of 5

The bare facts caused some of it; the skill, which wraps the same facts in
prose, caused more.

### The mechanism, in the answers' own words

The skill says *"the failure looks like a success"*, *"silently resets every
review in flight"*, *"records throttled holders as clean"*. It is three
paragraphs about **data being lost without anyone noticing**.

Every `with_skill` sample then declined to truncate a list in a different
package, and said why:

> "I did **not** apply `PAGE_LIMIT`, because truncating would silently drop
> in-window rows the brief says should be reported"

That is the skill's own vocabulary — *silently drop* — applied to a convention
the skill never mentions, in a package it never mentions. The skill did not
teach a fact that happened to be wrong elsewhere. It installed a **disposition**,
and the disposition travelled.

**A skill is not only its content. It is a standing bias on everything the model
does while it is loaded**, and the more vividly it argues its case, the further
that bias reaches. Nothing in this project's earlier design would have detected
that, because nothing else ran a task the skill was irrelevant to.

### Two of the three "absent" facts were not absent

| | `none` | `skill` | gap | |
|---|---:|---:|---:|---|
| a1 throttled is not clear | **100%** | 100% | **+0** | leaked |
| a2 pending_review never submitted | **0%** | 100% | +100 | clean |
| a3 null score is not clear | 40% | 100% | +60 | partly leaked |

**a1 leaked through the client's own docstring.** `certis.py` documents a
response as `{"status": "ok", "results": [...]}`, and a field named `status`
whose value is spelled out as `"ok"` announces that other values exist. All five
controls checked it unprompted. I built the fixture and did not see that the
example body was the tell.

**a3 leaked through an ambiguity I introduced.** The brief offers two outcomes,
`clear` and `unverified`, and Certis documents no threshold and no adverse
field — so "no adverse findings" is undefined. The controls split three ways on
what a `results` entry means, and two of the five happened to land on a reading
that reports null scores as unverified for unrelated reasons. Every single
sample flagged this gap in its notes. I cut a third outcome from the vocabulary
to reduce surface area, and that cut is what created the hole.

**Only a2 measured what it was built to measure**, and it measured it perfectly:
zero of five controls skipped a `pending_review` holder, five of five did with
the skill. The gates were cleared on the strength of one clean discriminator and
one accident.

### What this run is worth

- **The capture gate works and the skill passed it.** A skill can deliver
  everything the raw facts deliver. That is new information.
- **The harm gate works and caught something real.** A skill can be perfect on
  its own task and still not be worth installing.
- **"Absent information" is harder to construct than it looks.** Two of three
  facts leaked through an example body and a vocabulary choice, both mine, both
  invisible until fifteen subagents read them.

### What happens next, per the pre-registration

The registration says a missed gate means the skill does not ship, and it does
not. `candidates/certis-verification/` stays where it is.

This is not the F001–F003 pattern of rescuing a premise. The premise held: the
information was decisive (+53.3) and the skill delivered it (100%). What failed
is the *skill as written*, for a diagnosed and fixable reason, and fixing it is
what `skill-creator`'s iterate loop is for. The next version should carry the
same three facts in flatter prose, scoped explicitly to Certis, and be measured
against the same four gates — with a1 and a3 repaired first, since two of the
three discriminators in this run were not testing what they claimed.

---

## F005 — the leaks closed, the skill beat the oracle, and the fix for the harm caused a different harm. Not proven.

**2026-08-22. Fifteen blind `claude-opus-5` subagents, five per arm.** Same four
gates as F004, deliberately unchanged. An earlier attempt was killed by a spend
limit at 4/5 controls and 0/5 in both treatment arms; it was recorded as
[aborted](../eval/runs/F005/ABORTED.md) and not scored.

| arm | absent checks |
|---|---:|
| `without_skill` | **0/15 (0%)** |
| `oracle` | 11/15 (73.3%) |
| `with_skill` | **15/15 (100%)** |

| gate | bar | measured | |
|---|---|---:|---|
| task validity | ≥ +40 | **+73.3** | ok |
| lift | ≥ +40 | **+100.0** | MET |
| spread | ≥ 2 | **3** | MET |
| capture | ≥ 70% | **136%** | MET |
| **no harm** | ≥ −5 | **−8.3** | **REGRESSED** |

**NOT PROVEN**, on the same gate as F004 — but for a completely different
reason, and that is the finding.

### The repairs worked

F004's a1 measured +0 because the client docstring read `{"status": "ok", ...}`
and every control checked `status` unprompted. F004's a3 measured +60 through
an ambiguity in a two-outcome vocabulary. With `status` removed from the
documented shape and a third outcome added:

| | F004 | F005 |
|---|---:|---:|
| a1 throttled | +0 | **+100** |
| a2 pending_review | +100 | **+100** |
| a3 null score | +60 | **+100** |

**All three facts are now genuinely absent: the control scored 0% on every one
of them, in all five samples.** Four of five controls never looked for `status`
at all, against five of five that did in F004. That is what removing an example
value from a docstring is worth.

### The skill beat the oracle, and that is a wording defect, not a triumph

`with_skill` 100%, `oracle` 73.3%, so capture reads **136%**. It is not evidence
that packaging beats facts. The oracle text says *"verify() is not idempotent…
**calling it again** restarts that holder's review clock"*, and **four of five
oracle samples read "again" as "twice in one pass"** — memoising or capping at
one call rather than not calling. Skill v2 says *"Filter them out before
calling."*

The two treatments were not informationally equivalent on a2. The skill carried
a directive the oracle only implied. Any capture figure above 100% here is
measuring my oracle wording, and the fix is to make the oracle state the
consequence as plainly as the skill does.

One oracle sample also failed two functional checks by treating *any* present
`status` key as unverifiable, so `status: ok` bodies came back unverified. The
sanity floor caught it and it is included above, unweighted.

### The harm moved instead of shrinking

−13.3 in F004, −8.3 in F005. Still outside tolerance, and composed of entirely
different checks.

| | `none` | `oracle` | `skill` | F004 skill |
|---|---:|---:|---:|---:|
| c7 id-shape validation | 100% | 100% | **20%** | 80% |
| c8 newest-first | 100% | 100% | **60%** | 20% |
| c9 capped at PAGE_LIMIT | 20% | 40% | 40% | **0%** |

**F004's harm is gone.** The paging collapse that ran 3/5 → 2/5 → 0/5 is now
1/5 → 2/5 → 2/5: the skill arm pages *more* than the control. Removing the
vivid prose removed the disposition it installed.

**And a new harm appeared, caused by the fix.** On the unrelated task:

    arm             ids.valid   sorts   PAGE_LIMIT
    without_skill        5/5     5/5          1/5
    oracle               5/5     5/5          2/5
    with_skill           1/5     3/5          2/5

Skill v2 closes with a scope paragraph added specifically to stop spillover:

> They are not a general position on error handling, on **pagination**, on
> **ordering**, or on when to return partial results. **Follow this codebase's
> own conventions for all of that.**

Both halves backfired. *"Follow this codebase's own conventions"* points at the
**majority pattern** — `isinstance`, used by 24 of 27 modules — and away from
the **stated invariant** in `ids.py` that the key grades, so `ids.valid` fell
from 5/5 to 1/5. And naming *ordering* as something the skill has no view on
appears to have made ordering feel discretionary: sorting fell from 5/5 to 3/5.

> **A scope disclaimer is not neutral. Naming a topic in order to disclaim it
> still puts the topic in play**, and telling a model to follow "the codebase's
> conventions" tells it to follow the majority, which is not always what the
> codebase says about itself.

### An instrument bug, caught after it had produced a verdict

F005 was first scored with `is_harm = task["task"] != "t004"` hardcoded in the
adapter. t004 had been retired and replaced by t005, so **every** task matched,
the primary eval was emitted with all nine checks pooled rather than the three
absent ones, and a +100 absent lift came out as **+33.3 — failing a +40 bar.**

The verdict flipped on a hardcoded string, and the wrong verdict was the one I
saw first.

The correction is legitimate but it must be shown, not asserted: the bar was
registered "on the absent checks" in `design-F004.md:143`, and the adapter's own
docstring said it emitted absent checks only. Both were committed at
`6322933`, 03:15; t005 landed at `5f583a0`, 13:56, ten hours later. The
pre-registration is older than the bug, so this is implementing what was
registered rather than moving a bar — but **both numbers are recorded here**
because a correction made after seeing a failing result has to be checkable.

The adapter now reads the harm eval's name from the registration, and a test
fails if any task id is compared in adapter logic again. Mutation-checked.

### Standing

Four gates cleared. The premise is not in doubt: the information is decisive,
the packaging delivers it, and two runs now agree on that. What neither version
of the skill has managed is to sit in a context without changing unrelated
work — and the two failures had **opposite causes**, one from arguing too
vividly and one from disclaiming too explicitly.

The next version should carry the three facts with neither the argument nor the
scope paragraph, and be measured against the same four gates. If harm persists
a third time with the prose stripped to bare facts, the honest conclusion is
that **loading any skill costs something on unrelated work**, and the question
becomes what an acceptable price is rather than how to reach zero.
