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
    narrow conventions  demonstrated in only a handful of modules out of ~30.
                        A control has to happen to read the right file. C6-C8.

The oracle is handed all eight. The control gets whatever it read. If that
still produces no gap, breadth is not the explanation for F001 and the honest
reading is that the effect is not there -- which is written into
docs/prediction-F002.md before the run, not after it.

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

# (package, module, kind, functions)
#   kind: "current" follows all eight; "legacy" follows none.
PLAN = [
    ("accounts", "lookup", "current", ["find_account", "account_status"]),
    ("accounts", "limits", "current", ["credit_limit_micros", "raise_limit"]),
    ("accounts", "holders", "current", ["holder_of", "holder_email"]),
    ("accounts", "legacy_import", "legacy", ["import_account", "sync_holder"]),
    ("ledger", "entries", "current", ["entries_for", "entry_by_id"]),
    ("ledger", "totals", "current", ["posted_total_micros", "pending_total_micros"]),
    ("ledger", "history", "narrow_time", ["entries_since", "last_entry_at_ms"]),
    ("ledger", "legacy_rollup", "legacy", ["monthly_rollup", "rollup_csv"]),
    ("payouts", "schedule", "narrow_time", ["next_payout_at_ms", "payouts_due"]),
    ("payouts", "records", "narrow_order", ["payouts_for", "payout_by_id"]),
    ("payouts", "state", "current", ["mark_sent", "payout_state"]),
    ("payouts", "legacy_batch", "legacy", ["build_batch", "batch_totals"]),
    ("fx", "rates", "current", ["rate_for", "convert_micros"]),
    ("fx", "pairs", "narrow_ids", ["pair_exists", "pairs_for"]),
    ("fx", "legacy_quotes", "legacy", ["quote", "quote_table"]),
    ("invoices", "documents", "narrow_ids", ["invoice_by_id", "invoices_for"]),
    ("invoices", "lines", "current", ["lines_for", "line_total_micros"]),
    ("invoices", "dunning", "narrow_order", ["overdue_invoices", "dunning_stage"]),
    ("invoices", "legacy_pdf", "legacy", ["render_pdf", "pdf_path"]),
    ("notifications", "outbox", "narrow_order", ["queued_for", "oldest_queued"]),
    ("notifications", "delivery", "current", ["mark_delivered", "delivery_state"]),
    ("notifications", "legacy_smtp", "legacy", ["send_mail", "smtp_config"]),
    ("reporting", "summaries", "narrow_time", ["daily_summary", "summary_at_ms"]),
    ("reporting", "exports", "current", ["export_rows", "export_name"]),
    ("settlements", "batches", "current", ["batch_for", "batch_total_micros"]),
    ("settlements", "windows", "narrow_time", ["window_open_at_ms", "windows_for"]),
    ("settlements", "legacy_files", "legacy", ["write_file", "file_name"]),
    ("disputes", "cases", "narrow_ids", ["case_by_id", "cases_for"]),
    ("disputes", "evidence", "current", ["evidence_for", "evidence_count"]),
    ("disputes", "outcomes", "narrow_order", ["outcomes_for", "latest_outcome"]),
    ("webhooks", "endpoints", "current", ["endpoint_for", "endpoint_secret"]),
    ("webhooks", "deliveries", "narrow_order", ["deliveries_for", "last_delivery"]),
    ("webhooks", "legacy_retry", "legacy", ["retry_all", "retry_count"]),
    ("treasury", "balances", "current", ["balance_micros", "reserved_micros"]),
    ("treasury", "movements", "narrow_time", ["movements_since", "moved_at_ms"]),
    ("treasury", "legacy_recon", "legacy", ["reconcile", "recon_report"]),
]

# The task lives in `accounts`, and accounts/ deliberately contains NO narrow
# convention. This is the design decision the whole calibration turns on, so it
# is stated here rather than buried: a model that reads only the package it is
# working in will pick up C1-C5 and miss C6-C8, because those are demonstrated
# in ledger, payouts, fx, invoices, notifications, reporting, settlements,
# disputes, webhooks and treasury instead.
#
# That is realistic -- project-wide conventions are not re-demonstrated in
# every package -- but it is a choice, and if the control reads widely enough
# to find them anyway then breadth is not the explanation for F001 and the
# result should be read as such.

HEADER = '"""{title}\n\n{note}\n"""\nfrom __future__ import annotations\n\n'


def current_module(pkg, mod, fns, *, clock=False, order=False, ids=False):
    imports = ["from ..audit import audited",
               "from ..errors import E_INVALID, E_NOT_FOUND"]
    if ids:
        imports.append("from ..ids import valid")
    body = []
    for i, fn in enumerate(fns):
        arg = "account_id"
        sig = f"{fn}({arg}, clock)" if clock else f"{fn}({arg})"
        guard = (f'    if not valid("acc", {arg}):\n'
                 f'        return False, None, E_INVALID\n') if ids else (
                f'    if not isinstance({arg}, str) or not {arg}:\n'
                f'        return False, None, E_INVALID\n')
        if clock:
            inner = (f'    cutoff_ms = clock.now_ms() - 86_400_000\n'
                     f'    rows = [r for r in _ROWS if r["{pkg}_id"] == {arg}\n'
                     f'            and r["created_at_ms"] >= cutoff_ms]\n')
        else:
            inner = f'    rows = [r for r in _ROWS if r["{pkg}_id"] == {arg}]\n'
        if order:
            inner += ('    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)\n')
        tail = ('    if not rows:\n        return False, None, E_NOT_FOUND\n'
                '    return True, [dict(r) for r in rows], None\n'
                if i == 0 else
                '    if not rows:\n        return False, None, E_NOT_FOUND\n'
                '    return True, sum(r["amount_micros"] for r in rows), None\n')
        body.append(f"@audited\ndef {sig}:\n{guard}{inner}{tail}")
    # Neutral prose ONLY. An earlier draft had every current module recite the
    # conventions it demonstrates ("Amounts are micros; every export returns a
    # triple and is audited"), which meant one grep for "convention" handed a
    # control all eight and destroyed the breadth mechanism this fixture exists
    # to test. The conventions must be DEMONSTRATED in code and STATED nowhere.
    note = "Part of the {pkg} service.".format(pkg=pkg)
    return (HEADER.format(title=f"{pkg}.{mod} -- {mod.replace('_', ' ')}.", note=note)
            + "\n".join(imports) + "\n\n"
            + f'__all__ = {fns!r}\n\n'
            + '_ROWS = [\n'
            + "".join(
                f'    {{"id": "{pkg[:3]}_{i}", "{pkg}_id": "acc_10{i % 3}", '
                f'"amount_micros": {(i + 1) * 1_250_000}, '
                f'"created_at_ms": {1_720_000_000_000 + i * 3_600_000}}},\n'
                for i in range(4))
            + ']\n\n\n' + "\n\n".join(body))


def legacy_module(pkg, mod, fns):
    body = []
    for fn in fns:
        body.append(textwrap.dedent(f'''
            def {fn}(account_id):
                """Pre-2024 helper. Kept for the migration window."""
                if not account_id:
                    raise ValueError("account_id is required")
                rows = [r for r in _ROWS if r["account"] == account_id]
                if not rows:
                    raise LookupError("nothing for " + account_id)
                return sum(r["amount_cents"] for r in rows) / 100.0
        ''').strip())
    return (HEADER.format(
        title=f"{pkg}.{mod} -- legacy.",
        # Also neutral: the previous wording enumerated exactly which
        # conventions this file violates, which is the same leak in reverse.
        note="Pre-2024 helper, kept for the migration window.")
        + '_ROWS = [\n'
        + "".join(f'    {{"id": "old_{i}", "account": "acc_10{i % 3}", '
                  f'"amount_cents": {(i + 1) * 125}}},\n' for i in range(3))
        + ']\n\n\n' + "\n\n".join(body) + "\n")


def main() -> None:
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

    written = {"current": 0, "legacy": 0, "narrow_time": 0,
               "narrow_order": 0, "narrow_ids": 0}
    for pkg, mod, kind, fns in PLAN:
        pkg_dir = ROOT / pkg
        pkg_dir.mkdir(exist_ok=True)
        init = pkg_dir / "__init__.py"
        if not init.exists():
            init.write_text(f'"""{pkg}."""\n', encoding="utf-8", newline="\n")
        if kind == "legacy":
            src = legacy_module(pkg, mod, fns)
        else:
            src = current_module(
                pkg, mod, fns,
                clock=(kind == "narrow_time"),
                order=(kind == "narrow_order"),
                ids=(kind == "narrow_ids"))
        (pkg_dir / f"{mod}.py").write_text(src, encoding="utf-8", newline="\n")
        written[kind] += 1
    print("modules written:", written)
    print("total files:", sum(1 for _ in ROOT.rglob("*.py")))


if __name__ == "__main__":
    main()
