"""t001 -- available balance. Acceptance checks.

TWO KINDS, AND THE SPLIT IS THE WHOLE INSTRUMENT

    functional     the brief asks for it. Does the thing work at all.
    conventional   Meridian's house rules. NOT industry standard, NOT
                   guessable, and never stated in the brief.

`functional` is the sanity check that makes `conventional` readable: if an
answer cannot compute the right number, its convention score says nothing about
whether a skill carried the conventions across.

`conventional` is the discriminator, and it is the reason this fixture uses
arbitrary house rules rather than good practice. A model trained on the
internet already knows good practice -- that is precisely why the previous
project's evaluations all ceilinged. It cannot know that THIS codebase stores
money in micros and returns triples, so a control has somewhere to lose.
"""
import ast

CHECKS = [
    {"id": "f_computes_posted_total", "kind": "functional",
     "what": "acc_100 available balance is the sum of POSTED entries only.",
     "why": "The brief says posted entries only; led_3 is pending."},
    {"id": "f_unknown_account_is_a_failure", "kind": "functional",
     "what": "An unknown account does not come back as a success.",
     "why": "The brief says it must report failure for an unknown account."},

    {"id": "c_returns_a_triple", "kind": "conventional",
     "what": "Returns (ok, value, error), not a bare number.",
     "why": "Rule 2. Every public function in the codebase does this and the "
            "brief never mentions it."},
    {"id": "c_amount_is_micros", "kind": "conventional",
     "what": "The name carries the _micros suffix and the value is an int in "
             "micros, not cents and not a float.",
     "why": "Rule 1. Every amount in the fixture is micros; nothing says so."},
    {"id": "c_errors_are_codes", "kind": "conventional",
     "what": "Failure returns a constant from meridian.errors, not prose.",
     "why": "Rule 3. A free-text message is the natural thing to write and the "
            "wrong thing here."},
    {"id": "c_never_raises", "kind": "conventional",
     "what": "A bad argument returns E_INVALID rather than raising.",
     "why": "Rule 4. Raising is the Python-idiomatic answer and the one this "
            "codebase forbids."},
    {"id": "c_is_audited_and_exported", "kind": "conventional",
     "what": "Carries @audited and appears in __all__.",
     "why": "Rule 5. Invisible to compliance otherwise."},
]

FIXED_NOW_MS = 1_720_400_000_000
EXPECTED_MICROS = 95_500_000          # 125_500_000 - 30_000_000, pending excluded


def _fn(module):
    """The module's exported public function, whatever it is called.

    The first version guessed two names. A calibration answer that followed
    every house rule but called itself `available_micros` scored 0/5, which
    looked like a model failing to infer the conventions and was entirely a
    defect in this file. Grade what the brief constrains; it does not pin a
    name.
    """
    for name in list(getattr(module, "__all__", []) or []):
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    for name in dir(module):
        if name.startswith("_"):
            continue
        fn = getattr(module, name)
        if callable(fn) and getattr(fn, "__module__", "") == module.__name__:
            return fn
    return None


def check_f_computes_posted_total(module, src):
    """Deliberately UNIT-AGNOSTIC.

    Whether the answer is in micros is a convention question, scored by
    c_amount_is_micros. Conflating the two here would make a naive draft fail
    `functional` as well, and a run whose functional rate is not near ceiling
    cannot be read for conventions at all. So this asks only the functional
    question: were the right rows summed -- posted, excluding pending?
    """
    fn = _fn(module)
    assert fn is not None, "no available_balance* function"
    got = fn("acc_100")
    value = got[1] if isinstance(got, tuple) else got
    assert isinstance(value, (int, float)), f"no numeric result: {value!r}"
    micros = round(float(value) * 1_000_000) if abs(float(value)) < 1_000_000         else round(float(value))
    assert micros == EXPECTED_MICROS, (
        f"summed to {value!r}; want the POSTED entries only "
        f"({EXPECTED_MICROS} micros, or 95.5 in units). Including the pending "
        f"entry gives 105490000.")


def check_f_unknown_account_is_a_failure(module, src):
    fn = _fn(module)
    try:
        got = fn("acc_nope")
    except Exception:
        return  # raising is a failure signal; rule 4 scores that separately
    if isinstance(got, tuple):
        assert got[0] is False, f"unknown account reported success: {got!r}"
    else:
        assert got in (None, 0) or got is False, \
            f"unknown account returned a value: {got!r}"


def check_c_returns_a_triple(module, src):
    got = _fn(module)("acc_100")
    assert isinstance(got, tuple) and len(got) == 3, \
        f"returned {type(got).__name__} {got!r}, want a 3-tuple"
    assert got[0] is True and got[2] is None, f"success shape wrong: {got!r}"


def check_c_amount_is_micros(module, src):
    fn = _fn(module)
    assert fn.__name__.endswith("_micros") or \
        any(n.endswith("_micros") for n in getattr(module, "__all__", [])), \
        "no _micros suffix on the exported name"
    got = fn("acc_100")
    value = got[1] if isinstance(got, tuple) else got
    assert isinstance(value, int) and not isinstance(value, bool), \
        f"amount is {type(value).__name__}, want int micros"


def check_c_errors_are_codes(module, src):
    from meridian.errors import ALL_CODES
    got = _fn(module)("acc_nope")
    assert isinstance(got, tuple), "no triple, so no error code to check"
    assert got[2] in ALL_CODES, f"error {got[2]!r} is not a meridian.errors code"


def check_c_never_raises(module, src):
    fn = _fn(module)
    from meridian.errors import E_INVALID
    for bad in ("", None, 42):
        try:
            got = fn(bad)
        except Exception as exc:
            raise AssertionError(
                f"raised {type(exc).__name__} on {bad!r}; rule 4 says return "
                f"E_INVALID") from None
        assert isinstance(got, tuple) and got[0] is False and got[2] == E_INVALID, \
            f"{bad!r} returned {got!r}, want (False, None, E_INVALID)"


def check_c_is_audited_and_exported(module, src):
    """Grades what __all__ actually names, not a guessed function name.

    The first version looked for a function called available_balance*, so a
    conventional answer named available_micros failed a rule it had followed.
    """
    tree = ast.parse(src)
    exported = list(getattr(module, "__all__", []) or [])
    assert exported, "module defines no __all__"
    names = [n.name for n in ast.walk(tree)
             if isinstance(n, ast.FunctionDef) and n.name in exported]
    assert names, f"__all__ is {exported!r} but defines none of them here"
    decorated = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name in names
        and any(getattr(d, "id", getattr(d, "attr", None)) == "audited"
                for d in n.decorator_list)
    ]
    assert decorated, f"exported {names} but none is decorated with @audited"
