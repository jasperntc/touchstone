# F004 — information the codebase does not contain

Design and pre-registration. Written before the fixture is built, and before
anything is spawned.

## What changed, and why the question is different now

F001–F003 asked whether a skill restating a codebase's own conventions beats no
skill. Three fixtures, 22 blind subagents, no run cleared a bar set in advance.
The control read the tree and found the conventions — in F003 it scored 88% on
ten rules it was told nothing about, and the one rule it declined it had found
and *rejected on reasoning*, because that rule contradicted its instructions.

So the premise moves to the thing a codebase genuinely cannot supply.

**And that changes what is worth measuring.** If the information is truly absent,
`oracle` beats `none` *by construction* — of course facts help when nobody could
have deduced them. A large lift there is not a finding. Two things are:

| question | measured by |
|---|---|
| Is the information decisive at all, or does the model do fine without it? | `oracle` − `none`, and if it is small the **task** is rejected |
| Does the packaged **skill** deliver what the raw facts delivered? | `with_skill` − `none`, as a **fraction of** `oracle` − `none` |

The second is the one that has never been asked here, and it is exactly your
requirement #1. F001 already showed it is not automatic: handed rules verbatim,
that oracle scored *worse* than the control by misapplying one.

## The failure mode being targeted

Absent information only produces a measurable gap if the model, lacking it,
does something **confidently wrong** — not if it hesitates or asks. A task where
the control sensibly says "I don't know the rate limit, please confirm" measures
nothing.

So the fixture must offer a **plausible, attractive wrong path**, and the absent
information must be the only reason it is wrong.

## The fixture

Reuses `eval/fixture/meridian` — 54 files, already built. Its problem was the
conventions premise, not the codebase. Two additions:

**`meridian/vendor/certis.py`** — a thin client for an external KYC provider.
`CertisClient.verify(holder_id)` returns a dict. Nothing in the tree calls it
yet; this is a new integration, so there is **no precedent to copy**. That is
deliberate: F003 died partly on majority-versus-minority arguments about
existing code, and here there is no existing code to argue about.

**The task, `t004`** — write `verify_holders(account_ids, client, ...)` in
`meridian/compliance/reverify.py`, verifying each account's holder through
Certis and reporting the results.

The obvious implementation — loop the ids, call `verify` on each, collect —
is what a competent engineer writes, and it is wrong in three ways nothing in
the repository reveals.

## The absent information

Three facts. Each is operational, none is deducible, each makes the obvious
implementation fail in a specific gradeable way.

| | fact | what the obvious code does |
|---|---|---|
| **a1** | Certis rate-limits to 100 calls/minute per key, and on throttle returns **HTTP 200** with `{"status": "throttled", "results": []}` rather than an error | fires all calls in a burst, sees 200s, records empty results as "no match" |
| **a2** | `verify` is **not idempotent** for a holder already in `pending_review`: calling it again resets the review clock | re-verifies everyone, silently restarting reviews in flight |
| **a3** | a `null` in `results[].score` means **not checked**, not zero | records 0, which reads downstream as a failed check |

These are the shape of real runbook and incident knowledge: nothing in a
codebase carries them, they are learned by being told or by an outage.

## Grading

Three kinds, never blended:

- **functional** — a result for every requested id; unusable ids reported as
  failures. Passable without any of the three facts, so the control's
  competence is visible.
- **absent** — a1, a2, a3. These are the discriminators.
- **conventional** — two house rules F003 proved controls get unaided (the
  return triple, error codes). A sanity floor: if the control fails *these*,
  the run is broken, not informative.

`a1` is graded on the outcome, not the strategy: a throttled holder must not
be reported clear. Any approach that achieves that — pacing, retrying, or
reporting them as unverified — passes.

### Two defects caught before the fixture was finished

**The outcome vocabulary made a1 unfailable.** The first version used
{`verified`, `unverified`}, and under those words the naive draft passed a1 for
free: an empty results list reads naturally as "unverified", which is the safe
answer. The real-world harm is the opposite — an empty result from an identity
provider means *no adverse findings*, so the holder reads as clean. The words
are now {`clear`, `unverified`}, and a band of holders return `status: ok` with
an empty list so that "empty" alone is genuinely ambiguous and only `status`
separates a throttle from a clean pass. An answer that treats every empty list
as suspicious now fails a functional check instead.

**The store size entangled a1 with a2.** At 150 holders a correct answer skips
the 50 in `pending_review` and makes exactly 100 calls — precisely the budget —
so the throttle never fires for it, and a1 could only ever be observed in an
answer that had already failed a2. That is F002's second defect exactly. At 180
holders the correct answer still makes 120 calls and still meets the throttle.

Verified rather than assumed, with three drafts each knowing exactly one fact:

    draft knows      a1     a2     a3    | functional  floor
    nothing          ----   ----   ----  |    3/3       2/2
    a1 only          PASS   ----   ----  |    3/3       2/2
    a2 only          ----   PASS   ----  |    3/3       2/2
    a3 only          ----   ----   PASS  |    3/3       2/2

## The harm eval

`skills/` is a **collection**. A skill is installed into a project and then sits
there while unrelated work happens, so "does installing this make anything else
worse" is a question a single skill's own eval never asks and a collection must.

`t002` — the existing `recent_adjustments` task, which the Certis facts have
nothing to do with — runs as `harm_eval`. Its runs are held out of the primary
numbers entirely and checked separately for regression.

## The arms

| arm | gets |
|---|---|
| `without_skill` | the task and the codebase |
| `oracle` | the same, plus the three facts as plain text |
| `with_skill` | the same, plus a `SKILL.md` that has to carry those facts and get itself applied |

Prompts are assembled so the arms differ by the treatment block and nothing
else; `prereg.py --check-prompts` asserts it. Each run gets its own staged tree
via `stage.py --fanout`.

## Thresholds, fixed now

Registered in `eval/prereg/F004.json` and committed before anything is spawned.
`--verdict` refuses to score a run whose registration is later than the numbers.

| gate | bar | why this number |
|---|---|---|
| **task validity** | `oracle` − `without_skill` ≥ **+40** on the absent checks | Absent information should be worth far more than the +15 a conventions skill was asked for. Below +40 the facts are not decisive and the **task** is rejected — not the skill. |
| **skill delivers** | `with_skill` captures ≥ **70%** of that headroom | The new gate, and the real one. A skill that carries the facts but does not get itself applied fails here, and F001 showed that is a live outcome. |
| **spread** | ≥ **2** of the 3 absent checks show a ≥40 gap | F002 and F003 both produced a pooled ~+12 that was one expectation wearing an average as a disguise. |
| **no harm** | `t002` moves no worse than **−5** points with the skill installed | A skill that improves its own task and damages the rest of the project has not earned installation. |

Sample size: **5 runs per arm**, 15 subagents plus the harm eval. F003 used 5
and its per-expectation splits were clean at that size.

## What each outcome means, decided in advance

- **All four gates met.** The first proven skill. It gets a `RESULT.md` and
  enters `skills/`, and requirements #2–#8 unblock, because there is finally
  something to distribute and recommend.
- **Task validity missed.** The facts were not decisive — the model coped
  without them. That is a genuine and surprising finding, and it would mean
  operational knowledge is *also* not where skills earn their keep.
- **Task valid, capture missed.** The most informative failure available. The
  information helps and the skill format does not deliver it. That is a
  fixable authoring problem, not a dead premise, and it is what skill-creator's
  iterate loop exists for.
- **No-harm missed.** The skill works and costs more than it returns. It does
  not ship.

## The alternative premise, recorded so it is not lost

The skills that demonstrably work in the wild — `pdf`, `xlsx`, `docx` — do not
carry secret facts. They carry **executable scripts and a procedure with known
failure modes**. That is a third premise, distinct from both conventions and
absent information, and on the evidence so far it is the strongest of the three.

F004 tests absent information because that is the pre-registered next step and
because operational knowledge is what a project-specific collection would
actually hold. If F004's capture gate fails, the procedure-and-tooling premise
is the next one to run, and the instruments here need no changes to run it.
