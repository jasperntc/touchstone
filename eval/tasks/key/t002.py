"""t002 -- recent adjustments. Acceptance checks.

EVERY DEFECT IN F001 CAME FROM THIS FILE'S PREDECESSOR, SO THE RULES ARE STATED

1. Grade only what the brief constrains. The brief pins ONE name,
   `recent_adjustments`. It does not pin the parameter order, the extra
   parameters, or the row shape, so nothing here may either. F001 guessed at
   `available_balance*` and scored a fully conventional answer 0/5.

2. Behaviour over implementation. `c7_validates_id_shape` does not look for a
   call to ids.valid; it passes a malformed id and requires E_INVALID. An
   answer that reimplements the check correctly passes, as it should.

3. Call adaptively, once, through _call(). An answer that takes a clock and one
   that does not must both be reachable, or the grader measures signature
   fashion rather than conventions.

    functional     the brief says it. Right rows, right window.
    conventional   Meridian house rules the brief never mentions.

WHICH ACCOUNT EACH CHECK USES, AND WHY THEY DIFFER

F002's second instrument defect was a convention entangled with correctness,
and adding a cap (C9) and a zero-filter (C10) is a fresh chance to make that
mistake: under those rules the conventional answer and the literal reading of
the brief return DIFFERENT rows. So each check gets an account where only the
thing it is testing varies.

    acc_102   3 rows in window, none zero, fewer than PAGE_LIMIT. Neither C9
              nor C10 changes the answer, so this is where FUNCTIONAL
              correctness and ordering (C8) are graded.
    acc_101   6 rows in window, none zero. Only C9 changes the answer here.
    acc_103   3 rows in window, one of them exactly 0. Only C10 changes it.
    acc_104   one row, 40 days old. Nothing in window: the failure path.

C8, C9 and C10 are structurally independent -- a sort, a slice and a filter --
and are graded on three different accounts, so failing one does not
mechanically fail the others. That matters: F002's single discriminator made
"the effect" and "one convention" the same number.
"""
import inspect
import time

CHECKS = [
    {"id": "f_selects_the_right_rows", "kind": "functional",
     "what": "acc_102 within 7 days is exactly adj_21, adj_22, adj_23.",
     "why": "The brief pins the window and the account filter. Chosen so that "
            "neither the cap nor the zero-filter alters the answer."},
    {"id": "f_missing_rows_is_a_failure", "kind": "functional",
     "what": "acc_104, whose only row is 40 days old, is reported as a failure.",
     "why": "The brief says so outright. Stronger than an unknown account: it "
            "separates 'no rows in window' from 'no such account'."},

    {"id": "c1_amounts_are_micros", "kind": "conventional",
     "what": "Row amounts stay int micros; nothing is divided into units.",
     "why": "C1. Wide -- visible in most modules. F002: found by all controls."},
    {"id": "c2_returns_a_triple", "kind": "conventional",
     "what": "Returns (ok, value, error).",
     "why": "C2. Wide. F002: found by all controls."},
    {"id": "c3_errors_are_codes", "kind": "conventional",
     "what": "Failure carries a meridian.errors constant, not prose.",
     "why": "C3. Wide. F002: found by all controls."},
    {"id": "c4_never_raises", "kind": "conventional",
     "what": "Unusable input returns E_INVALID instead of raising.",
     "why": "C4. Wide. F002: found by all controls."},
    {"id": "c5_audited_and_exported", "kind": "conventional",
     "what": "The exported function is @audited and named in __all__.",
     "why": "C5. Wide. F002: found by all controls."},

    {"id": "c6_uses_an_injected_clock", "kind": "conventional",
     "what": "Takes a clock and computes the window from clock.now_ms().",
     "why": "C6. Narrow -- 5 of 27 current modules, none in accounts/. F002: "
            "found by both clean controls anyway, because a clock parameter "
            "is VISIBLE IN A SIGNATURE. Checked structurally: the store "
            "anchors to wall time so both time bases select the same rows, "
            "which keeps this a convention question and not a correctness one."},
    {"id": "c7_validates_id_shape", "kind": "conventional",
     "what": "A wrong-prefix or malformed id is E_INVALID, not merely absent.",
     "why": "C7. Narrow -- 3 of 27, none in accounts/. F002: found by both "
            "clean controls anyway; an ids.valid call is visible on the first "
            "line of any function that has one."},

    {"id": "c8_newest_first", "kind": "conventional",
     "what": "acc_102's rows come back ordered by created_at_ms, newest first.",
     "why": "C8. Narrow -- 5 of 27, none in accounts/. F002: MISSED by both "
            "clean controls, and it was the entire measured gap. Not visible "
            "in any signature; you learn it only by reading what a function "
            "does to rows after it has them. The store lists acc_102 "
            "scrambled so an answer that never sorts cannot pass by accident."},
    {"id": "c9_capped_at_page_limit", "kind": "conventional",
     "what": "acc_101 has 6 rows in window; a listing returns PAGE_LIMIT of them.",
     "why": "C9. Narrow -- 5 of 27, none in accounts/. Graded on LENGTH only, "
            "not on which rows, so it does not double-count C8: an answer "
            "that caps without sorting passes this and fails C8, and one that "
            "sorts without capping does the reverse."},
    {"id": "c10_zero_rows_are_not_listed", "kind": "conventional",
     "what": "acc_103's zero-amount row adj_32 is absent; the other two present.",
     "why": "C10. Narrow -- 3 of 27, none in accounts/. The 'other two "
            "present' half is load-bearing: without it an answer that returns "
            "nothing at all would pass for free, which is how F002's c8 nearly "
            "went unnoticed."},
]

# The five conventions demonstrated ONLY outside accounts/. `--drafts` requires
# the partial draft to fail exactly this set: not a subset, not a superset. An
# edit that makes one of them visible in the task's own package, or makes a
# wide convention accidentally hard, changes what a null result means, and this
# is the line that notices.
NARROW = [
    "c6_uses_an_injected_clock",
    "c7_validates_id_shape",
    "c8_newest_first",
    "c9_capped_at_page_limit",
    "c10_zero_rows_are_not_listed",
]

DISCRIMINATING = "conventional"

FN_NAME = "recent_adjustments"

WINDOW_DAYS = 7
FUNCTIONAL_ACCOUNT = "acc_102"
IN_WINDOW = ["adj_21", "adj_22", "adj_23"]        # acc_102, within 7 days
NEWEST_FIRST = ["adj_21", "adj_22", "adj_23"]     # -1d, -3d, -6d
EMPTY_WINDOW_ACCOUNT = "acc_104"                  # one row, 40 days old

CAP_ACCOUNT = "acc_101"
CAP_IN_WINDOW = ["adj_11", "adj_12", "adj_13", "adj_14", "adj_15", "adj_16"]

ZERO_ACCOUNT = "acc_103"
ZERO_ROW = "adj_32"
ZERO_KEEPERS = ["adj_31", "adj_33"]


class _Clock:
    """Reports wall time, which is what the store anchors to at import.

    Not a pinned past instant: that would make every wall-time answer
    functionally wrong and entangle C6 with correctness. See _store.py.
    """
    def now_ms(self):
        return int(time.time() * 1000)


def _fn(module):
    fn = getattr(module, FN_NAME, None)
    assert callable(fn), "no callable named {!r} (the brief pins it)".format(FN_NAME)
    return fn


def _call(module, account_id, days=WINDOW_DAYS):
    """Invoke the answer whatever shape it chose, and say how.

    Returns (result, took_clock). Never raises for a signature mismatch -- a
    grader that cannot call an answer has measured nothing.

    The window is passed to the first non-clock parameter after the account id
    EVEN IF IT HAS A DEFAULT. An earlier version let defaults stand, so an
    answer that made the window optional with a default of 30 would have been
    graded on a 30-day window and failed a FUNCTIONAL check for a reason that
    was really about signature taste. The brief pins that a days parameter
    exists; the grader uses it.
    """
    fn = _fn(module)
    params = list(inspect.signature(fn).parameters.values())
    names = [p.name for p in params]
    took_clock = any("clock" in n for n in names)

    args, kwargs, window_given = [], {}, False
    for i, p in enumerate(params):
        if i == 0:
            args.append(account_id)
        elif "clock" in p.name:
            kwargs[p.name] = _Clock()
        elif not window_given:
            kwargs[p.name] = days
            window_given = True
        elif p.default is inspect.Parameter.empty:
            kwargs[p.name] = None
    try:
        return fn(*args, **kwargs), took_clock
    except TypeError:
        for attempt in ((account_id, _Clock(), days), (account_id, days, _Clock()),
                        (account_id, days), (account_id,)):
            try:
                return fn(*attempt), took_clock
            except TypeError:
                continue
        raise AssertionError("could not call {} with any plausible argument "
                             "order; signature is {}".format(FN_NAME, names))


def _rows(result):
    value = result[1] if isinstance(result, tuple) and len(result) == 3 else result
    assert isinstance(value, (list, tuple)), "no row list in {!r}".format(result)
    return list(value)


def _ids(rows):
    out = []
    for r in rows:
        if isinstance(r, dict):
            out.append(r.get("id"))
        else:
            out.append(getattr(r, "id", None))
    return out


def check_f_selects_the_right_rows(module, src):
    result, _ = _call(module, FUNCTIONAL_ACCOUNT)
    got = _ids(_rows(result))
    assert sorted(x for x in got if x) == sorted(IN_WINDOW), (
        "selected {}, want {} (adj_24 is 20 days old; the rest belong to "
        "other accounts)".format(got, IN_WINDOW))


def check_f_missing_rows_is_a_failure(module, src):
    try:
        result, _ = _call(module, EMPTY_WINDOW_ACCOUNT)
    except Exception:
        return  # raising is a failure signal; c4 scores that separately
    if isinstance(result, tuple) and len(result) == 3:
        assert result[0] is False, (
            "an account with nothing in the window reported success: "
            "{!r}".format(result))
    else:
        assert not result, (
            "an account with nothing in the window returned rows: "
            "{!r}".format(result))


def check_c1_amounts_are_micros(module, src):
    result, _ = _call(module, FUNCTIONAL_ACCOUNT)
    for row in _rows(result):
        amount = row.get("amount_micros") if isinstance(row, dict) else None
        assert amount is not None, "row has no amount_micros: {!r}".format(row)
        assert isinstance(amount, int) and not isinstance(amount, bool), \
            "amount_micros is {}, want int micros".format(type(amount).__name__)


def check_c2_returns_a_triple(module, src):
    result, _ = _call(module, FUNCTIONAL_ACCOUNT)
    assert isinstance(result, tuple) and len(result) == 3, \
        "returned {}, want a 3-tuple".format(type(result).__name__)
    assert result[0] is True and result[2] is None, \
        "success shape: {!r}".format(result)


def check_c3_errors_are_codes(module, src):
    from meridian.errors import ALL_CODES
    try:
        result, _ = _call(module, "acc_999")
    except Exception:
        raise AssertionError("raised instead of returning an error code") from None
    assert isinstance(result, tuple) and len(result) == 3, "no triple to carry a code"
    assert result[2] in ALL_CODES, \
        "error {!r} is not a meridian.errors code".format(result[2])


def check_c4_never_raises(module, src):
    from meridian.errors import E_INVALID
    for bad in ("", None, 42, []):
        try:
            result, _ = _call(module, bad)
        except AssertionError:
            raise
        except Exception as exc:
            raise AssertionError(
                "raised {} on {!r}; C4 says return E_INVALID".format(
                    type(exc).__name__, bad)) from None
        assert isinstance(result, tuple) and result[0] is False \
            and result[2] == E_INVALID, \
            "{!r} returned {!r}, want (False, None, E_INVALID)".format(bad, result)


def check_c5_audited_and_exported(module, src):
    import ast
    exported = list(getattr(module, "__all__", []) or [])
    assert FN_NAME in exported, \
        "__all__ is {!r} and omits {}".format(exported, FN_NAME)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == FN_NAME:
            names = [getattr(d, "id", getattr(d, "attr", None))
                     for d in node.decorator_list]
            assert "audited" in names, \
                "decorators are {}, want @audited".format(names)
            return
    raise AssertionError("{} is not defined in this module".format(FN_NAME))


def check_c6_uses_an_injected_clock(module, src):
    result, took_clock = _call(module, FUNCTIONAL_ACCOUNT)
    assert took_clock, ("takes no clock parameter, so the window is computed "
                        "from wall time")
    assert _ids(_rows(result)), \
        "clock accepted but no rows selected from the supplied instant"


def check_c7_validates_id_shape(module, src):
    from meridian.errors import E_INVALID
    for bad in ("xyz_101", "acc_", "acc101"):
        result, _ = _call(module, bad)
        assert isinstance(result, tuple) and len(result) == 3, \
            "{!r} returned {!r}, no triple".format(bad, result)
        assert result[2] == E_INVALID, (
            "{!r} returned {!r}; a malformed id is E_INVALID, not merely an "
            "account with no rows".format(bad, result[2]))


def check_c8_newest_first(module, src):
    result, _ = _call(module, FUNCTIONAL_ACCOUNT)
    got = _ids(_rows(result))
    assert got == NEWEST_FIRST, \
        "order is {}, want newest first {}".format(got, NEWEST_FIRST)


def check_c9_capped_at_page_limit(module, src):
    from meridian.paging import PAGE_LIMIT
    assert len(CAP_IN_WINDOW) > PAGE_LIMIT, "fixture no longer exercises the cap"
    result, _ = _call(module, CAP_ACCOUNT)
    got = [x for x in _ids(_rows(result)) if x]
    assert set(got) <= set(CAP_IN_WINDOW), (
        "returned {} for {}, which includes rows outside the window or rows "
        "belonging to other accounts".format(got, CAP_ACCOUNT))
    assert len(got) == PAGE_LIMIT, (
        "{} has {} rows in the window and the listing returned {}; C9 caps a "
        "listing at PAGE_LIMIT={}".format(
            CAP_ACCOUNT, len(CAP_IN_WINDOW), len(got), PAGE_LIMIT))


def check_c10_zero_rows_are_not_listed(module, src):
    result, _ = _call(module, ZERO_ACCOUNT)
    got = [x for x in _ids(_rows(result)) if x]
    for keeper in ZERO_KEEPERS:
        assert keeper in got, (
            "{} is missing from {}; this check must not be passable by "
            "returning nothing".format(keeper, got))
    assert ZERO_ROW not in got, (
        "{} has amount_micros 0 and appears in {}; C10 keeps zero-amount rows "
        "out of listings".format(ZERO_ROW, got))
