"""t005 -- Certis re-verification, with F004's two leaks closed.

WHAT CHANGED FROM t004, AND WHY

F004 cleared its lift, spread and capture gates and still told a muddy story,
because two of its three "absent" facts were not absent.

    a1  measured +0. All five controls checked `status` unprompted. The client
        docstring read {"status": "ok", ...}, and a field whose value is
        spelled out announces that other values exist. The example body was the
        tell. `status` is now absent from the documented shape while remaining
        present in real responses -- documentation lagging an API, which is
        where this kind of knowledge actually lives.

    a3  measured +60, and not for the intended reason. The vocabulary was
        {clear, unverified} with no slot for "checked, and adverse", so "no
        adverse findings" was undefined; the controls split THREE ways on what
        a `results` entry meant and two of them passed a3 by accident. Every
        sample flagged the gap in its notes.

So the outcome vocabulary is now three-valued and `adverse` is an explicit
documented boolean. `f_an_adverse_holder_is_flagged` is the check that makes
the third value load-bearing: an answer that collapses `flagged` into
`unverified` -- which is what F004 forced everyone to do -- now fails a
FUNCTIONAL check rather than accidentally passing an absent one.

WHAT IS STILL WITHHELD

    a1  a throttled call is HTTP 200 with an undocumented "status" key set to
        "throttled" and an empty results list -- indistinguishable from a clean
        answer unless you know the key is there.
    a2  verify() is not idempotent for a holder in pending_review.
    a3  a null score means NOT CHECKED. `adverse: false` alongside it does not
        mean clean; nothing was checked to be clean about.

BAND LAYOUT, SO THE CHECKS STAY INDEPENDENT

120 settled holders, budget 100:

    index   0- 9   null score        a3
    index  10-29   empty results     functional decoy: must be `clear`
    index  30-49   adverse: true     functional: must be `flagged`
    index  50-119  ordinary clear
    calls 101+     throttled         a1

The throttle band falls inside the ordinary range, so it cannot overlap a3's or
either functional band on any forward pass. `_confounded()` asserts that rather
than assuming it.
"""
import inspect

FN_NAME = "verify_holders"
BUDGET = 100
NULL_BAND = 10
CLEAR_BAND = 20
ADVERSE_BAND = 20

CLEAR, FLAGGED, UNVERIFIED = "clear", "flagged", "unverified"

DISCRIMINATING = "absent"

CHECKS = [
    {"id": "f_reports_every_account", "kind": "functional",
     "what": "Every requested account id appears in the result.",
     "why": "The brief says an outcome is reported for every account given."},
    {"id": "f_a_clean_holder_is_clear", "kind": "functional",
     "what": "Holders Certis answers for with an empty results list are clear.",
     "why": "The decoy. Without it, an answer that calls every empty list "
            "suspicious would pass a1 for the wrong reason -- which is exactly "
            "what three of F004's five controls did."},
    {"id": "f_an_adverse_holder_is_flagged", "kind": "functional",
     "what": "Holders whose result carries adverse=true are reported flagged.",
     "why": "This is what F004 had no slot for. It makes the third outcome "
            "load-bearing, so an answer that collapses adverse into unverified "
            "fails HERE rather than passing a3 by accident."},
    {"id": "f_unusable_ids_are_failures", "kind": "functional",
     "what": "An id with no holder, and a malformed id, are reported.",
     "why": "The brief says so outright."},

    {"id": "c2_returns_a_triple", "kind": "conventional",
     "what": "Returns (ok, value, error).",
     "why": "House rule, and a sanity floor. F003 measured every control "
            "getting this unaided; a control failing it means the run is "
            "broken, not that a skill helped."},
    {"id": "c3_errors_are_codes", "kind": "conventional",
     "what": "A failure carries a meridian.errors constant, not prose.",
     "why": "Same. Floor, not discriminator."},

    {"id": "a1_throttled_is_not_an_answer", "kind": "absent",
     "what": "Throttled holders are reported unverified -- neither clear nor "
             "flagged.",
     "why": "ABSENT, and genuinely so this time. The `status` key is not in the "
            "documented response shape at all, so a throttled body is an empty "
            "results list and nothing else."},
    {"id": "a2_pending_review_is_never_submitted", "kind": "absent",
     "what": "No holder in pending_review was passed to client.verify.",
     "why": "ABSENT. verify() is not idempotent for them. Graded from the call "
            "log, so any avoiding strategy passes. This was F004's one clean "
            "discriminator: 0 of 5 controls, 5 of 5 with the skill."},
    {"id": "a3_null_score_is_not_clear", "kind": "absent",
     "what": "Holders whose result carries score=None are not reported clear.",
     "why": "ABSENT. null means not checked, and `adverse: false` beside it "
            "asserts nothing -- there was no check to be clean of."},
]

ABSENT = [c["id"] for c in CHECKS if c["kind"] == "absent"]


class FakeCertis:
    """A Certis client that behaves the way the three absent facts say it does."""

    def __init__(self, holders):
        self._state = {h["holder_id"]: h["review_state"] for h in holders}
        settled = [h["holder_id"] for h in holders
                   if h["review_state"] == "settled"]
        a, b = NULL_BAND, NULL_BAND + CLEAR_BAND
        self._null = set(settled[:a])
        self._empty = set(settled[a:b])
        self._adverse = set(settled[b:b + ADVERSE_BAND])
        self.calls, self.throttled = [], []
        self.null_scored, self.empty_but_ok, self.adverse_hits = [], [], []

    def _row(self, holder_id, score, adverse):
        return {"holder_id": holder_id, "score": score, "adverse": adverse}

    def verify(self, holder_id):
        self.calls.append(holder_id)
        if len(self.calls) > BUDGET:
            self.throttled.append(holder_id)
            return {"status": "throttled", "results": []}
        if holder_id in self._null:
            self.null_scored.append(holder_id)
            return {"status": "ok",
                    "results": [self._row(holder_id, None, False)]}
        if holder_id in self._empty:
            self.empty_but_ok.append(holder_id)
            return {"status": "ok", "results": []}
        if holder_id in self._adverse:
            self.adverse_hits.append(holder_id)
            return {"status": "ok", "results": [self._row(holder_id, 22, True)]}
        return {"status": "ok", "results": [self._row(holder_id, 91, False)]}

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


def _accounts(holder_ids):
    state = {h["holder_id"]: h["account_id"] for h in _holders()}
    return [state[h] for h in holder_ids if h in state]


def _confounded(client):
    graded = set(client.null_scored) | set(client.empty_but_ok) | \
        set(client.adverse_hits)
    overlap = set(client.throttled) & graded
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
    wrong = [a for a in _accounts(client.empty_but_ok) if got.get(a) != CLEAR]
    assert not wrong, (
        "{} holder(s) Certis answered for with nothing to report were not "
        "clear, e.g. {}. An empty results list is a clean answer.".format(
            len(wrong), wrong[:3]))


def check_f_an_adverse_holder_is_flagged(module, src):
    result, client = _run(module)
    _confounded(client)
    assert client.adverse_hits, "GRADER PROBLEM: no adverse holder was reached"
    got = _outcomes(result)
    wrong = [a for a in _accounts(client.adverse_hits) if got.get(a) != FLAGGED]
    assert not wrong, (
        "{} holder(s) carrying adverse=true were not flagged, e.g. {}. "
        "Collapsing an adverse finding into another outcome loses the one "
        "thing the pass exists to surface.".format(len(wrong), wrong[:3]))


def check_f_unusable_ids_are_failures(module, src):
    result, _ = _run(module, ids=["acc_200", "acc_999999", "nope"])
    got = _outcomes(result)
    for bad in ("acc_999999", "nope"):
        assert bad in got, "{!r} was dropped rather than reported".format(bad)
        assert got[bad] not in (CLEAR, FLAGGED), \
            "{!r} has no holder and was reported {!r}".format(bad, got[bad])


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


def check_a1_throttled_is_not_an_answer(module, src):
    result, client = _run(module)
    _confounded(client)
    assert client.throttled, (
        "GRADER PROBLEM: nothing was throttled, so this check could not fail. "
        "{} call(s) against a budget of {}.".format(len(client.calls), BUDGET))
    got = _outcomes(result)
    wrong = [a for a in _accounts(client.throttled)
             if got.get(a) in (CLEAR, FLAGGED)]
    assert not wrong, (
        "{} of {} throttled holder(s) were reported as an answer, e.g. {}. A "
        "throttled call returns an empty results list and an undocumented "
        "status key; nothing about the holder was established.".format(
            len(wrong), len(client.throttled), wrong[:3]))


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
    wrong = [a for a in _accounts(client.null_scored) if got.get(a) == CLEAR]
    assert not wrong, (
        "{} of {} holder(s) with a null score were reported clear, e.g. {}. "
        "A null score means not checked; adverse=false beside it asserts "
        "nothing.".format(len(wrong), len(client.null_scored), wrong[:3]))
