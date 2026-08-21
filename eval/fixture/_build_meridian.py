#!/usr/bin/env python3
"""Generate the Meridian fixture.

WHY THIS IS GENERATED RATHER THAN HAND-WRITTEN

The fixture's job is to be too large to read exhaustively while keeping the
convention distribution EXACTLY known. Hand-writing thirty modules would make
the second part a guess, and the whole calibration turns on it: if I cannot say
which convention is visible in which file, I cannot say what a control that
read four files should have been able to infer.

THE SCALING MECHANISM, STATED PLAINLY SO IT CAN BE ARGUED WITH

F001 failed because six small files could be read end to end, so the control
inferred every convention and the oracle had nothing to add. The fix is NOT to
hide information -- that would test telepathy. It is BREADTH:

    wide conventions    demonstrated in most modules. A control that reads any
                        two or three current files will pick these up, and
                        SHOULD. C1-C5.
    narrow conventions  demonstrated in a handful of modules out of 36. A
                        control has to happen to read the right file. C6-C10.

The oracle is handed all ten. The control gets whatever it read.

WHAT F002 CHANGED HERE, AND THE RISK THAT CREATES

F002 ran this fixture with three narrow conventions and the controls found two
of them unaided -- the injected clock and id-shape validation -- by reading
outside the package they were working in. Only ORDERING survived, and one
convention out of eight is not a foundation.

Looking at which survived, the split is not narrow-vs-wide at all:

    found by controls   micros naming, return triples, error codes, no-raise,
                        @audited, a `clock` parameter, an ids.valid call.
                        Every one is VISIBLE AT A GLANCE in any module that
                        happens to be open -- in a signature, a return
                        statement, a decorator line.
    missed by controls  ordering. Not visible in any signature. You only learn
                        it by tracing what a function does to rows after it
                        has them.

So the distinction that predicts the result is legibility, not rarity, and
F003's two new conventions are drawn from the same category as the one that
worked: a slice (C9) and a filter (C10), both invisible from outside a
function, both structurally independent of the sort (C8) so that missing one
does not mechanically mean missing the others.

THIS IS A SELECTION EFFECT AND IT IS DECLARED, NOT HIDDEN. Choosing new
conventions because they resemble the one that produced a gap makes a gap more
likely, and a result engineered that way says less than it appears to. Two
things keep it honest, both fixed before the run in docs/prediction-F003.md:
the wide conventions stay in the fixture and in the denominator, so the primary
threshold is the same +15 on the same full conventional rate F002 was judged
against; and every narrow convention must be DEMONSTRATED in committed code a
reader can actually reach. Nothing here is knowable only by being told -- that
would be a different experiment, and an easier one.

LEGACY MODULES

A third of the tree predates the conventions and violates them, because a real
codebase does. This is realistic rather than adversarial: the legacy files are
a minority, they are not the newest, and nothing forces a reader to sample them
first. They exist so that "copy whatever the nearest file does" is not a
reliable strategy -- which is the actual situation a project-conventions skill
would exist to fix.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "meridian"

# How many rows a listing returns. Small enough that the fixture's own row sets
# exercise it, which is the point: a cap nothing ever hits is not demonstrated.
PAGE_LIMIT = 4

# (package, module, kind, narrow tags, functions)
#
#   kind    "current" follows the conventions; "legacy" follows none.
#   tags    which NARROW conventions this module demonstrates.
#             time   C6  takes a clock, computes the window from clock.now_ms()
#             ids    C7  validates id shape through ids.valid
#             order  C8  sorts rows newest first
#             page   C9  returns at most PAGE_LIMIT rows, after sorting
#             zero   C10 omits rows whose amount_micros is 0
#
# `page` and `order` overlap in three modules and are independent in two, which
# is the realistic shape -- you usually sort before you cap -- while still
# leaving a reader able to find one without the other.
PLAN = [
    ("accounts", "lookup", "current", (), ["find_account", "account_status"]),
    ("accounts", "limits", "current", (), ["credit_limit_micros", "raise_limit"]),
    ("accounts", "holders", "current", (), ["holder_of", "holder_email"]),
    ("accounts", "legacy_import", "legacy", (), ["import_account", "sync_holder"]),

    ("ledger", "entries", "current", (), ["entries_for", "entry_by_id"]),
    ("ledger", "totals", "current", (), ["posted_total_micros", "pending_total_micros"]),
    ("ledger", "history", "current", ("time",), ["entries_since", "last_entry_at_ms"]),
    ("ledger", "legacy_rollup", "legacy", (), ["monthly_rollup", "rollup_csv"]),

    ("payouts", "schedule", "current", ("time",), ["next_payout_at_ms", "payouts_due"]),
    ("payouts", "records", "current", ("order", "page"), ["payouts_for", "payout_by_id"]),
    ("payouts", "state", "current", (), ["mark_sent", "payout_state"]),
    ("payouts", "legacy_batch", "legacy", (), ["build_batch", "batch_totals"]),

    ("fx", "rates", "current", (), ["rate_for", "convert_micros"]),
    ("fx", "pairs", "current", ("ids",), ["pair_exists", "pairs_for"]),
    ("fx", "legacy_quotes", "legacy", (), ["quote", "quote_table"]),

    ("invoices", "documents", "current", ("ids",), ["invoice_by_id", "invoices_for"]),
    ("invoices", "lines", "current", ("zero",), ["lines_for", "line_total_micros"]),
    ("invoices", "dunning", "current", ("order",), ["overdue_invoices", "dunning_stage"]),
    ("invoices", "legacy_pdf", "legacy", (), ["render_pdf", "pdf_path"]),

    ("notifications", "outbox", "current", ("order", "page"), ["queued_for", "oldest_queued"]),
    ("notifications", "delivery", "current", (), ["mark_delivered", "delivery_state"]),
    ("notifications", "legacy_smtp", "legacy", (), ["send_mail", "smtp_config"]),

    ("reporting", "summaries", "current", ("time", "zero"), ["daily_summary", "summary_at_ms"]),
    ("reporting", "exports", "current", ("page",), ["export_rows", "export_name"]),

    ("settlements", "batches", "current", (), ["batch_for", "batch_total_micros"]),
    ("settlements", "windows", "current", ("time",), ["window_open_at_ms", "windows_for"]),
    ("settlements", "legacy_files", "legacy", (), ["write_file", "file_name"]),

    ("disputes", "cases", "current", ("ids",), ["case_by_id", "cases_for"]),
    ("disputes", "evidence", "current", ("zero",), ["evidence_for", "evidence_count"]),
    ("disputes", "outcomes", "current", ("order",), ["outcomes_for", "latest_outcome"]),

    ("webhooks", "endpoints", "current", (), ["endpoint_for", "endpoint_secret"]),
    ("webhooks", "deliveries", "current", ("order", "page"), ["deliveries_for", "last_delivery"]),
    ("webhooks", "legacy_retry", "legacy", (), ["retry_all", "retry_count"]),

    ("treasury", "balances", "current", (), ["balance_micros", "reserved_micros"]),
    ("treasury", "movements", "current", ("time", "page"), ["movements_since", "moved_at_ms"]),
    ("treasury", "legacy_recon", "legacy", (), ["reconcile", "recon_report"]),
]

# The task lives in `accounts`, and accounts/ deliberately carries NO narrow
# tag. This is the design decision the whole calibration turns on, so it is
# stated here rather than buried: a model that reads only the package it is
# working in will pick up C1-C5 and miss C6-C10, because those are demonstrated
# in ledger, payouts, fx, invoices, notifications, reporting, settlements,
# disputes, webhooks and treasury instead.
#
# That is realistic -- project-wide conventions are not re-demonstrated in
# every package -- but it is a choice. F002 established that controls DO read
# outside their package and DO find C6 and C7 there, so the mechanism is not
# "the control cannot reach it"; it is "the control has to notice it is there."

HEADER = '"""{title}\n\n{note}\n"""\nfrom __future__ import annotations\n\n'


def _rows_literal(pkg, many, zero):
    """Row data for a generated module.

    A module tagged `page` gets more rows than PAGE_LIMIT and a module tagged
    `zero` gets a zero-amount row, so that in both cases the line demonstrating
    the convention actually does something. A cap that never truncates and a
    filter that never drops anything are not demonstrations; they are dead code
    a reader is entitled to ignore.
    """
    # Rows spread over `slots` accounts. A `page` module needs at least one
    # account holding MORE than PAGE_LIMIT rows or the slice never truncates,
    # and the zero row has to sit on an account that also holds a non-zero
    # one, or the filter turns a listing into a not-found instead of a
    # short list. Neither line would be a demonstration otherwise.
    slots = 2 if many else 3
    count = 2 * PAGE_LIMIT + 2 if many else 4
    zero_at = slots  # the first index that repeats an account
    out = []
    for i in range(count):
        amount = 0 if (zero and i == zero_at) else (i + 1) * 1_250_000
        out.append(
            '    {{"id": "{p}_{i}", "{pkg}_id": "acc_10{m}", '
            '"amount_micros": {a}, "created_at_ms": {t}}},\n'.format(
                p=pkg[:3], i=i, pkg=pkg, m=i % slots, a=amount,
                t=1_720_000_000_000 + i * 3_600_000))
    return "_ROWS = [\n" + "".join(out) + "]\n"


def current_module(pkg, mod, fns, tags):
    time_, ids_ = "time" in tags, "ids" in tags
    order_, page_, zero_ = "order" in tags, "page" in tags, "zero" in tags

    imports = ["from ..audit import audited",
               "from ..errors import E_INVALID, E_NOT_FOUND"]
    if ids_:
        imports.append("from ..ids import valid")
    if page_:
        imports.append("from ..paging import PAGE_LIMIT")

    body = []
    for i, fn in enumerate(fns):
        arg = "account_id"
        sig = "{}({}, clock)".format(fn, arg) if time_ else "{}({})".format(fn, arg)
        guard = ('    if not valid("acc", {a}):\n'
                 '        return False, None, E_INVALID\n'.format(a=arg)) if ids_ else (
                '    if not isinstance({a}, str) or not {a}:\n'
                '        return False, None, E_INVALID\n'.format(a=arg))

        clauses = ['r["{pkg}_id"] == {a}'.format(pkg=pkg, a=arg)]
        if time_:
            clauses.append('r["created_at_ms"] >= cutoff_ms')
        if zero_:
            clauses.append('r["amount_micros"] != 0')
        head = '    cutoff_ms = clock.now_ms() - 86_400_000\n' if time_ else ''
        inner = head + '    rows = [r for r in _ROWS\n            if ' + \
            '\n            and '.join(clauses) + ']\n'
        if order_:
            inner += '    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)\n'
        if page_:
            inner += '    rows = rows[:PAGE_LIMIT]\n'

        tail = ('    if not rows:\n        return False, None, E_NOT_FOUND\n'
                '    return True, [dict(r) for r in rows], None\n'
                if i == 0 else
                '    if not rows:\n        return False, None, E_NOT_FOUND\n'
                '    return True, sum(r["amount_micros"] for r in rows), None\n')
        body.append("@audited\ndef {}:\n{}{}{}".format(sig, guard, inner, tail))

    # Neutral prose ONLY. An earlier draft had every current module recite the
    # conventions it demonstrates ("Amounts are micros; every export returns a
    # triple and is audited"), which meant one grep for "convention" handed a
    # control all of them and destroyed the breadth mechanism this fixture
    # exists to test. The conventions must be DEMONSTRATED in code and STATED
    # nowhere. eval/harness/stage.py --audit re-checks that on every push.
    note = "Part of the {pkg} service.".format(pkg=pkg)
    return (HEADER.format(title="{}.{} -- {}.".format(pkg, mod, mod.replace("_", " ")),
                          note=note)
            + "\n".join(imports) + "\n\n"
            + "__all__ = {!r}\n\n".format(fns)
            + _rows_literal(pkg, page_, zero_)
            + "\n\n" + "\n\n".join(body))


def legacy_module(pkg, mod, fns):
    body = []
    for fn in fns:
        body.append(textwrap.dedent('''
            def {fn}(account_id):
                """Pre-2024 helper. Kept for the migration window."""
                if not account_id:
                    raise ValueError("account_id is required")
                rows = [r for r in _ROWS if r["account"] == account_id]
                if not rows:
                    raise LookupError("nothing for " + account_id)
                return sum(r["amount_cents"] for r in rows) / 100.0
        ''').strip().format(fn=fn))
    return (HEADER.format(
        title="{}.{} -- legacy.".format(pkg, mod),
        # Also neutral: the previous wording enumerated exactly which
        # conventions this file violates, which is the same leak in reverse.
        note="Pre-2024 helper, kept for the migration window.")
        + '_ROWS = [\n'
        + "".join('    {{"id": "old_{i}", "account": "acc_10{m}", '
                  '"amount_cents": {c}}},\n'.format(i=i, m=i % 3, c=(i + 1) * 125)
                  for i in range(3))
        + ']\n\n\n' + "\n\n".join(body) + "\n")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "__init__.py").write_text(
        '"""Meridian -- internal ledger platform."""\n', encoding="utf-8", newline="\n")

    (ROOT / "errors.py").write_text(textwrap.dedent('''
        """Error codes. Every failure in current Meridian code is one of these."""

        E_NOT_FOUND = "E_NOT_FOUND"
        E_INVALID = "E_INVALID"
        E_CONFLICT = "E_CONFLICT"
        E_FORBIDDEN = "E_FORBIDDEN"
        E_UNAVAILABLE = "E_UNAVAILABLE"

        ALL_CODES = (E_NOT_FOUND, E_INVALID, E_CONFLICT, E_FORBIDDEN, E_UNAVAILABLE)
    ''').lstrip(), encoding="utf-8", newline="\n")

    (ROOT / "paging.py").write_text(textwrap.dedent('''
        """How much a listing hands back."""

        PAGE_LIMIT = {limit}
    ''').lstrip().format(limit=PAGE_LIMIT), encoding="utf-8", newline="\n")

    (ROOT / "audit.py").write_text(textwrap.dedent('''
        """The audit decorator. Every current export wears one."""
        from __future__ import annotations

        import functools

        _LOG: list[dict] = []


        def audited(fn):
            """Record every call to an exported function."""
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                ok, value, error = fn(*args, **kwargs)
                _LOG.append({"fn": fn.__name__, "ok": ok, "error": error})
                return ok, value, error
            return wrapper


        def audit_log() -> list[dict]:
            return list(_LOG)
    ''').lstrip(), encoding="utf-8", newline="\n")

    (ROOT / "ids.py").write_text(textwrap.dedent('''
        """Identifier shapes. Every current entry point validates through here."""
        from __future__ import annotations

        PREFIXES = ("acc", "led", "pay", "inv", "ntf", "fx")


        def valid(prefix: str, value) -> bool:
            """True when `value` is a well-formed id with the given prefix."""
            if prefix not in PREFIXES:
                return False
            if not isinstance(value, str) or not value:
                return False
            head, _, rest = value.partition("_")
            return head == prefix and rest.isalnum() and len(rest) > 0
    ''').lstrip(), encoding="utf-8", newline="\n")

    (ROOT / "clock.py").write_text(textwrap.dedent('''
        """The only source of time in current Meridian code."""
        from __future__ import annotations


        class Clock:
            def now_ms(self) -> int:
                raise NotImplementedError


        class FixedClock(Clock):
            def __init__(self, now_ms: int) -> None:
                self._now_ms = now_ms

            def now_ms(self) -> int:
                return self._now_ms
    ''').lstrip(), encoding="utf-8", newline="\n")

    tally = {"current": 0, "legacy": 0}
    narrow = {"time": 0, "ids": 0, "order": 0, "page": 0, "zero": 0}
    for pkg, mod, kind, tags, fns in PLAN:
        pkg_dir = ROOT / pkg
        pkg_dir.mkdir(exist_ok=True)
        init = pkg_dir / "__init__.py"
        if not init.exists():
            init.write_text('"""{}."""\n'.format(pkg), encoding="utf-8", newline="\n")
        if kind == "legacy":
            src = legacy_module(pkg, mod, fns)
        else:
            src = current_module(pkg, mod, fns, tags)
        (pkg_dir / "{}.py".format(mod)).write_text(src, encoding="utf-8", newline="\n")
        tally[kind] += 1
        for t in tags:
            narrow[t] += 1

    in_accounts = [t for pkg, _, _, tags, _ in PLAN if pkg == "accounts" for t in tags]
    assert not in_accounts, (
        "accounts/ demonstrates {} -- the task package must be clean or the "
        "narrow conventions are not narrow".format(in_accounts))

    print("modules:", tally)
    print("narrow demonstrated in:", narrow, "of", tally["current"], "current modules")
    print("total files:", sum(1 for _ in ROOT.rglob("*.py")))
    print("accounts/ demonstrates no narrow convention: ok")


if __name__ == "__main__":
    main()
