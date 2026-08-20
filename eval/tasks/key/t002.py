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

Wide conventions (C1-C5) are visible all over the tree; a control SHOULD get
them and getting them is not evidence of anything. The discriminators are the
narrow ones -- C6 clock, C7 id shape, C8 ordering -- demonstrated nowhere in
the accounts package the task lives in.
"""
import inspect
import time

CHECKS = [
    {"id": "f_selects_the_right_rows", "kind": "functional",
     "what": "acc_101 within 7 days is exactly adj_1, adj_2, adj_5.",
     "why": "The brief pins the window and the account filter."},
    {"id": "f_missing_rows_is_a_failure", "kind": "functional",
     "what": "An account with nothing in the window is reported as a failure.",
     "why": "The brief says so outright."},

    {"id": "c1_amounts_are_micros", "kind": "conventional",
     "what": "Row amounts stay int micros; nothing is divided into units.",
     "why": "C1. Wide -- visible in most modules."},
    {"id": "c2_returns_a_triple", "kind": "conventional",
     "what": "Returns (ok, value, error).",
     "why": "C2. Wide."},
    {"id": "c3_errors_are_codes", "kind": "conventional",
     "what": "Failure carries a meridian.errors constant, not prose.",
     "why": "C3. Wide."},
    {"id": "c4_never_raises", "kind": "conventional",
     "what": "Unusable input returns E_INVALID instead of raising.",
     "why": "C4. Wide."},
    {"id": "c5_audited_and_exported", "kind": "conventional",
     "what": "The exported function is @audited and named in __all__.",
     "why": "C5. Wide."},
    {"id": "c6_uses_an_injected_clock", "kind": "conventional",
     "what": "Takes a clock and computes the window from clock.now_ms(), so a "
             "pinned clock changes the answer.",
     "why": "C6. NARROW -- demonstrated in 5 of 36 modules, none of them in "
            "accounts/. Checked STRUCTURALLY, by whether a clock parameter "
            "exists: the store anchors to wall time so both time bases "
            "select the same rows, which is deliberate -- it keeps this a "
            "convention question instead of a correctness one."},
    {"id": "c7_validates_id_shape", "kind": "conventional",
     "what": "A wrong-prefix or malformed id is E_INVALID, not merely absent.",
     "why": "C7. NARROW -- ids.valid is used in 3 of 36 modules, none in "
            "accounts/. A plain truthy-string guard accepts 'xyz_101'."},
    {"id": "c8_newest_first", "kind": "conventional",
     "what": "Rows come back ordered by created_at_ms, newest first.",
     "why": "C8. NARROW -- 5 of 36 modules sort; none in accounts/. The "
            "store lists acc_101 SCRAMBLED (adj_5, adj_2, adj_1 in source "
            "order) precisely so an answer that never sorts cannot pass "
            "this by accident."},
]

FN_NAME = "recent_adjustments"
DAY_MS = 86_400_000
IN_WINDOW = ["adj_1", "adj_2", "adj_5"]        # acc_101, within 7 days
NEWEST_FIRST = ["adj_1", "adj_2", "adj_5"]     # -1d, -3d, -6d


class _Clock:
    """Reports wall time, which is what the store anchors to at import.

    Not a pinned past instant: that would make every wall-time answer
    functionally wrong and entangle C6 with correctness. See _store.py.
    """
    def now_ms(self):
        return int(time.time() * 1000)


def _fn(module):
    fn = getattr(module, FN_NAME, None)
    assert callable(fn), f"no callable named {FN_NAME!r} (the brief pins it)"
    return fn


def _call(module, account_id, days=7):
    """Invoke the answer whatever shape it chose, and say how.

    Returns (result, took_clock). Never raises for a signature mismatch -- a
    grader that cannot call an answer has measured nothing.
    """
    fn = _fn(module)
    params = list(inspect.signature(fn).parameters.values())
    names = [p.name for p in params]
    took_clock = any("clock" in n for n in names)

    kwargs, positional = {}, []
    for i, p in enumerate(params):
        if i == 0:
            positional.append(account_id)
        elif "clock" in p.name:
            kwargs[p.name] = _Clock()
        elif p.default is inspect.Parameter.empty:
            positional.append(days)
        else:
            pass  # optional and not a clock: let the answer's default stand
    try:
        return fn(*positional, **kwargs), took_clock
    except TypeError:
        for attempt in ((account_id, _Clock(), days), (account_id, days, _Clock()),
                        (account_id, days), (account_id,)):
            try:
                return fn(*attempt), took_clock
            except TypeError:
                continue
        raise AssertionError(f"could not call {FN_NAME} with any plausible "
                             f"argument order; signature is {names}")


def _rows(result):
    value = result[1] if isinstance(result, tuple) and len(result) == 3 else result
    assert isinstance(value, (list, tuple)), f"no row list in {result!r}"
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
    result, _ = _call(module, "acc_101", 7)
    got = _ids(_rows(result))
    assert sorted(x for x in got if x) == sorted(IN_WINDOW), (
        f"selected {got}, want {IN_WINDOW} (adj_3 is 30 days old, adj_4 is a "
        f"different account)")


def check_f_missing_rows_is_a_failure(module, src):
    try:
        result, _ = _call(module, "acc_999", 7)
    except Exception:
        return  # raising is a failure signal; c4 scores that separately
    if isinstance(result, tuple) and len(result) == 3:
        assert result[0] is False, f"unknown account reported success: {result!r}"
    else:
        assert not result, f"unknown account returned rows: {result!r}"


def check_c1_amounts_are_micros(module, src):
    result, _ = _call(module, "acc_101", 7)
    for row in _rows(result):
        amount = row.get("amount_micros") if isinstance(row, dict) else None
        assert amount is not None, f"row has no amount_micros: {row!r}"
        assert isinstance(amount, int) and not isinstance(amount, bool), \
            f"amount_micros is {type(amount).__name__}, want int micros"


def check_c2_returns_a_triple(module, src):
    result, _ = _call(module, "acc_101", 7)
    assert isinstance(result, tuple) and len(result) == 3, \
        f"returned {type(result).__name__}, want a 3-tuple"
    assert result[0] is True and result[2] is None, f"success shape: {result!r}"


def check_c3_errors_are_codes(module, src):
    from meridian.errors import ALL_CODES
    try:
        result, _ = _call(module, "acc_999", 7)
    except Exception:
        raise AssertionError("raised instead of returning an error code") from None
    assert isinstance(result, tuple) and len(result) == 3, "no triple to carry a code"
    assert result[2] in ALL_CODES, f"error {result[2]!r} is not a meridian.errors code"


def check_c4_never_raises(module, src):
    from meridian.errors import E_INVALID
    for bad in ("", None, 42, []):
        try:
            result, _ = _call(module, bad, 7)
        except AssertionError:
            raise
        except Exception as exc:
            raise AssertionError(
                f"raised {type(exc).__name__} on {bad!r}; C4 says return "
                f"E_INVALID") from None
        assert isinstance(result, tuple) and result[0] is False \
            and result[2] == E_INVALID, \
            f"{bad!r} returned {result!r}, want (False, None, E_INVALID)"


def check_c5_audited_and_exported(module, src):
    import ast
    exported = list(getattr(module, "__all__", []) or [])
    assert FN_NAME in exported, f"__all__ is {exported!r} and omits {FN_NAME}"
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == FN_NAME:
            names = [getattr(d, "id", getattr(d, "attr", None))
                     for d in node.decorator_list]
            assert "audited" in names, f"decorators are {names}, want @audited"
            return
    raise AssertionError(f"{FN_NAME} is not defined in this module")


def check_c6_uses_an_injected_clock(module, src):
    result, took_clock = _call(module, "acc_101", 7)
    assert took_clock, ("takes no clock parameter, so the window is computed "
                        "from wall time")
    rows = _rows(result)
    assert _ids(rows), "clock accepted but no rows selected from the pinned instant"


def check_c7_validates_id_shape(module, src):
    from meridian.errors import E_INVALID
    for bad in ("xyz_101", "acc_", "acc101"):
        result, _ = _call(module, bad, 7)
        assert isinstance(result, tuple) and len(result) == 3, \
            f"{bad!r} returned {result!r}, no triple"
        assert result[2] == E_INVALID, (
            f"{bad!r} returned {result[2]!r}; a malformed id is E_INVALID, not "
            f"merely an account with no rows")


def check_c8_newest_first(module, src):
    result, _ = _call(module, "acc_101", 7)
    got = _ids(_rows(result))
    assert got == NEWEST_FIRST, f"order is {got}, want newest first {NEWEST_FIRST}"
