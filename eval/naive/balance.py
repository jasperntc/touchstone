"""Naive draft for t001. Calibration only -- never shown to an answerer.

Competent, idiomatic Python written by someone who has not been told Meridian's
house rules. It sums the right rows, so it clears the functional floor; it
raises, returns a bare float in currency units, and skips @audited/__all__,
so it fails the conventions.

That combination is exactly what a control condition should look like, and a
fixture where this draft scores well on `conventional` is a fixture that cannot
separate anything.
"""
from __future__ import annotations

from .ledger import entries_for


def available_balance(account_id):
    """Return the account's available balance in currency units."""
    if not account_id:
        raise ValueError("account_id must be a non-empty string")
    ok, rows, error = entries_for(account_id)
    if not ok:
        raise LookupError(f"no such account: {account_id}")
    posted = sum(r["amount_micros"] for r in rows if r["state"] == "posted")
    return posted / 1_000_000
