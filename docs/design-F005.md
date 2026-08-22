# F005 — the same skill, said flatly, against a repaired fixture

Two changes from [F004](findings.md), and the thresholds are **deliberately
identical** so the comparison is between the artifacts, not between two bars.

## What was repaired in the fixture

**a1 was never absent.** `certis.py` documented a response as
`{"status": "ok", ...}`, and a field whose value is spelled out announces that
other values exist. All five F004 controls checked it unprompted, and a1
measured +0. The `status` key is now absent from the documented shape while
still present in real responses — documentation lagging an API, which is where
this kind of knowledge actually lives.

**a3 was measuring an ambiguity I introduced.** The vocabulary was
`{clear, unverified}` with no slot for "checked, and adverse", so "no adverse
findings" was undefined; the controls split three ways and two passed a3 by
accident. There are now three outcomes and an explicit documented `adverse`
boolean, and `f_an_adverse_holder_is_flagged` makes the third value
load-bearing — an answer that collapses `flagged` into `unverified` now fails a
**functional** check instead of passing an absent one by luck.

Independence re-verified, functional pinned throughout:

    draft knows      a1     a2     a3    | functional  floor
    nothing          ----   ----   ----  |    4/4       2/2
    a1 only          PASS   ----   ----  |    4/4       2/2
    a2 only          ----   PASS   ----  |    4/4       2/2
    a3 only          ----   ----   PASS  |    4/4       2/2

## What changed in the skill

F004's skill delivered 100% of the oracle's headroom and then cost the
unrelated task 13.3 points, dose-dependently — 3 of 5 controls applied a paging
convention, 2 of 5 given bare facts, 0 of 5 given the skill. The mechanism was
its prose: *"the failure looks like a success"*, *"silently resets"*. Every
sample carrying it then refused to truncate a list in another package because
truncating would "silently drop" rows.

v2 carries the same three facts and drops the argument. Every loaded phrase is
gone, each rule names `CertisClient.verify` explicitly, and it closes with a
scope paragraph saying the rules are not a general position on error handling,
pagination, ordering or partial results. v1 is kept at
`eval/runs/F004/skill-v1.md`.

**The hypothesis this tests: the spillover was carried by the framing, not by
the facts.** If v2 clears the harm gate while keeping capture at or near 100%,
that is a usable authoring rule. If capture drops with it, the framing was
doing real work on the skill's own task too, and the trade is the finding.

## What would falsify the diagnosis

- **Harm persists at v2.** Then the spillover is not about vivid prose, and the
  likelier cause is topical adjacency — any skill about losing data biases any
  decision about dropping rows, however flatly it is written.
- **Capture falls below 70%.** Flat prose is worse at getting itself applied,
  and the vividness that caused the harm was also doing the work.
- **The control's t002 score moves.** It should not; the control sees no
  treatment at all. If it does, the harm measurement is noise and F004's −13.3
  needs re-reading.

Fifteen subagents, five per arm, `claude-opus-5`, same as F004.
