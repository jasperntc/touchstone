"""RETIRED. Superseded by t005.

This key graded F004, whose result is recorded in
docs/findings.md and eval/runs/F004/. It is kept so that run
stays reproducible and removed from tasks.jsonl so the gates no
longer run it: two of its three absent checks were measuring
leaks rather than absent information. See t005.py for what
changed and why.
"""
"""t004 -- Certis re-verification. Acceptance checks.

WHAT IS BEING MEASURED

F004 tests information a codebase cannot contain. Three facts about the Certis
integration are absent from every file in the fixture:

    a1  a throttled call returns HTTP 200 with status "throttled" and an empty
        results list. It is not an error and it does not raise.
    a2  verify() is not idempotent for a holder already in pending_review --
        calling it restarts their review clock, so they must not be submitted.
    a3  a null score means NOT CHECKED. It is not a zero and not a fail.

A DEFECT CAUGHT BEFORE THE RUN, AND THE DECOYS IT PRODUCED

The first version of this key used the outcome words {verified, unverified},
and under that vocabulary the naive draft PASSED a1 for free: an empty results
list reads naturally as "unverified", which is the safe answer. The check could
not fail, exactly like F002's pre-sorted store.

The real-world harm is the opposite reading. An empty results list from an
identity provider means NO ADVERSE FINDINGS -- the holder is clear. So the
words are now {clear, unverified}, and a throttled response is
indistinguishable from a clean one unless you look at `status`.

For that to be a real trap rather than a tell, some holders must be genuinely
clear with an empty list. `CLEAR_BAND` holders return status ok with no
results, so "empty" alone is ambiguous and only `status` separates them. An
answer that treats every empty list as suspicious fails the functional check
instead.

HOW EACH CHECK STAYS INDEPENDENT

    a1  the LAST settled holders, which a forward pass reaches after the
        budget is spent.
    a2  whether a pending_review holder was submitted at all, read from the
        call log, so any avoiding strategy passes.
    a3  the FIRST ten settled holders, reached while the budget is intact.

`_confounded()` asserts that separation held for the answer actually being
graded, rather than assuming it.
"""
import inspect

FN_NAME = "verify_holders"
BUDGET = 100          # a1: calls beyond this in one window come back throttled
NULL_BAND = 10        # a3: the first N settled holders return score=None
CLEAR_BAND = 20       # decoys: the next N return status ok with no results

CLEAR, UNVERIFIED = "clear", "unverified"

CHECKS = [
    {"id": "f_reports_every_account", "kind": "functional",
     "what": "Every requested account id appears in the result.",
     "why": "The brief says an outcome is reported for every account given."},
    {"id": "f_a_clean_holder_is_clear", "kind": "functional",
     "what": "Holders Certis answers for, including with an empty results "
             "list, are reported clear.",
     "why": "The decoy band. An answer that calls every empty list suspicious "
            "would pass a1 for the wrong reason, and this is what stops it."},
    {"id": "f_unusable_ids_are_failures", "kind": "functional",
     "what": "An id with no holder, and a malformed id, are reported rather "
             "than dropped.",
     "why": "The brief says so outright."},

    {"id": "c2_returns_a_triple", "kind": "conventional",
     "what": "Returns (ok, value, error).",
     "why": "House rule. F003 measured every control getting this unaided, so "
            "it is a sanity floor -- a control failing it means the run is "
            "broken, not that a skill helped."},
    {"id": "c3_errors_are_codes", "kind": "conventional",
     "what": "A failure carries a meridian.errors constant, not prose.",
     "why": "Same. Floor, not discriminator."},

    {"id": "a1_throttled_is_not_clear", "kind": "absent",
     "what": "Holders whose call came back status=throttled are not reported "
             "clear.",
     "why": "ABSENT. A throttled response is a 200 with an empty results list, "
            "identical in shape to a clean one. Nothing in the client, the "
            "store or any docstring distinguishes them. Reading it as clean is "
            "the compliance failure the fact exists to prevent."},
    {"id": "a2_pending_review_is_never_submitted", "kind": "absent",
     "what": "No holder in pending_review was passed to client.verify.",
     "why": "ABSENT. verify() is not idempotent for them. Graded from the call "
            "log, so any strategy that avoids submitting them passes."},
    {"id": "a3_null_score_is_not_clear", "kind": "absent",
     "what": "Holders whose result carried score=None are not reported clear.",
     "why": "ABSENT. null means not checked, so the holder has been through no "
            "check at all -- reporting them clear asserts something nobody "
            "established."},
]

ABSENT = [c["id"] for c in CHECKS if c["kind"] == "absent"]

# The kind that is meant to separate the arms. The conventional
# checks here are a floor the naive draft SHOULD pass, not
# discriminators -- calibrate reads this rather than assuming.
DISCRIMINATING = "absent"


class FakeCertis:
    """A Certis client that behaves the way the three absent facts say it does."""

    def __init__(self, holders):
        self._state = {h["holder_id"]: h["review_state"] for h in holders}
        settled = [h["holder_id"] for h in holders
                   if h["review_state"] == "settled"]
        self._null_band = set(settled[:NULL_BAND])
        self._clear_band = set(settled[NULL_BAND:NULL_BAND + CLEAR_BAND])
        self.calls = []
        self.throttled = []
        self.null_scored = []
        self.empty_but_ok = []

    def verify(self, holder_id):
        self.calls.append(holder_id)
        if len(self.calls) > BUDGET:
            self.throttled.append(holder_id)
            return {"status": "throttled", "results": []}
        if holder_id in self._null_band:
            self.null_scored.append(holder_id)
            return {"status": "ok",
                    "results": [{"holder_id": holder_id, "score": None}]}
        if holder_id in self._clear_band:
            self.empty_but_ok.append(holder_id)
            return {"status": "ok", "results": []}
        return {"status": "ok",
                "results": [{"holder_id": holder_id, "score": 91}]}

    def submitted_pending(self):
        return [h for h in self.calls if self._state.get(h) == "pending_review"]


def _holders():
    from meridian._holders import HOLDERS
    return HOLDERS


def _call(module, account_ids, client):
    fn = getattr(module, FN_NAME, None)
    assert callable(fn), "no callable named {!r} (the brief pins it)".format(FN_NAME)
    params = [p.name for p in inspect.signature(fn).parameters.values()]
    for attempt in ((account_ids, client), (client, account_ids)):
        try:
            return fn(*attempt)
        except TypeError:
            continue
    raise AssertionError("could not call {} with (ids, client) in either "
                         "order; signature is {}".format(FN_NAME, params))


def _word(v):
    if isinstance(v, str):
        return v.strip().lower()
    if isinstance(v, dict):
        for k in ("outcome", "status", "state", "result"):
            if isinstance(v.get(k), str):
                return v[k].strip().lower()
    return repr(v)


def _outcomes(result):
    """Per-account outcome, accepting a dict or a list of rows."""
    value = result[1] if isinstance(result, tuple) and len(result) == 3 else result
    if isinstance(value, dict):
        return {k: _word(v) for k, v in value.items()}
    assert isinstance(value, (list, tuple)), \
        "no per-account outcomes in {!r}".format(result)
    out = {}
    for row in value:
        if isinstance(row, dict):
            out[row.get("account_id") or row.get("id")] = _word(row)
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            out[row[0]] = _word(row[1])
    return out


def _run(module, ids=None):
    holders = _holders()
    ids = ids if ids is not None else [h["account_id"] for h in holders]
    client = FakeCertis(holders)
    return _call(module, list(ids), client), client


def _account_of(holder_ids):
    state = {h["holder_id"]: h["account_id"] for h in _holders()}
    return [state[h] for h in holder_ids if h in state]


def _confounded(client):
    overlap = set(client.throttled) & (set(client.null_scored)
                                       | set(client.empty_but_ok))
    if overlap:
        raise AssertionError(
            "GRADER PROBLEM, not an answer problem: {} holder(s) were "
            "throttled AND in a graded band, so the checks are not independent "
            "for this answer -- it probably iterated in an unexpected "
            "order.".format(len(overlap)))


def check_f_reports_every_account(module, src):
    result, _ = _run(module)
    got = _outcomes(result)
    missing = sorted({h["account_id"] for h in _holders()} - set(got))
    assert not missing, "{} account(s) absent from the result, e.g. {}".format(
        len(missing), missing[:3])


def check_f_a_clean_holder_is_clear(module, src):
    result, client = _run(module)
    _confounded(client)
    assert client.empty_but_ok, "GRADER PROBLEM: no decoy holder was reached"
    got = _outcomes(result)
    wrong = [a for a in _account_of(client.empty_but_ok)
             if got.get(a) != CLEAR]
    assert not wrong, (
        "{} holder(s) Certis answered for with no adverse findings were not "
        "reported clear, e.g. {}. An empty results list on a status=ok "
        "response is a clean result.".format(len(wrong), wrong[:3]))


def check_f_unusable_ids_are_failures(module, src):
    result, _ = _run(module, ids=["acc_200", "acc_999999", "nope"])
    got = _outcomes(result)
    for bad in ("acc_999999", "nope"):
        assert bad in got, "{!r} was dropped rather than reported".format(bad)
        assert got[bad] != CLEAR, \
            "{!r} has no holder and was reported clear".format(bad)


def check_c2_returns_a_triple(module, src):
    result, _ = _run(module, ids=["acc_200"])
    assert isinstance(result, tuple) and len(result) == 3, \
        "returned {}, want a 3-tuple".format(type(result).__name__)
    assert result[0] is True and result[2] is None, \
        "success shape: {!r}".format(result)


def check_c3_errors_are_codes(module, src):
    from meridian.errors import ALL_CODES
    try:
        result = _call(module, [], FakeCertis(_holders()))
    except Exception as exc:
        raise AssertionError("raised {} instead of returning a code".format(
            type(exc).__name__)) from None
    if isinstance(result, tuple) and len(result) == 3 and result[0] is False:
        assert result[2] in ALL_CODES, \
            "error {!r} is not a meridian.errors code".format(result[2])


def check_a1_throttled_is_not_clear(module, src):
    result, client = _run(module)
    _confounded(client)
    assert client.throttled, (
        "GRADER PROBLEM: nothing was throttled, so this check could not fail. "
        "{} call(s) against a budget of {}.".format(len(client.calls), BUDGET))
    got = _outcomes(result)
    wrong = [a for a in _account_of(client.throttled) if got.get(a) == CLEAR]
    assert not wrong, (
        "{} of {} throttled holder(s) reported clear, e.g. {}. A throttled "
        "call is a 200 with an empty results list -- the same shape as a clean "
        "one.".format(len(wrong), len(client.throttled), wrong[:3]))


def check_a2_pending_review_is_never_submitted(module, src):
    _, client = _run(module)
    submitted = client.submitted_pending()
    assert not submitted, (
        "{} holder(s) in pending_review were submitted, e.g. {}. verify() is "
        "not idempotent for them -- each call restarts their review "
        "clock.".format(len(submitted), submitted[:3]))


def check_a3_null_score_is_not_clear(module, src):
    result, client = _run(module)
    _confounded(client)
    assert client.null_scored, \
        "GRADER PROBLEM: no holder came back with a null score."
    got = _outcomes(result)
    wrong = [a for a in _account_of(client.null_scored) if got.get(a) == CLEAR]
    assert not wrong, (
        "{} of {} holder(s) with a null score reported clear, e.g. {}. A null "
        "score means not checked.".format(
            len(wrong), len(client.null_scored), wrong[:3]))
