"""ledger.legacy_rollup -- legacy.

Predates the current conventions. Amounts are cents, failures raise, and nothing here is audited. Do not copy this shape into new code; it is scheduled for removal.
"""
from __future__ import annotations

_ROWS = [
    {"id": "old_0", "account": "acc_100", "amount_cents": 125},
    {"id": "old_1", "account": "acc_101", "amount_cents": 250},
    {"id": "old_2", "account": "acc_102", "amount_cents": 375},
]


def monthly_rollup(account_id):
    """Pre-2024 helper. Kept for the migration window."""
    if not account_id:
        raise ValueError("account_id is required")
    rows = [r for r in _ROWS if r["account"] == account_id]
    if not rows:
        raise LookupError("nothing for " + account_id)
    return sum(r["amount_cents"] for r in rows) / 100.0

def rollup_csv(account_id):
    """Pre-2024 helper. Kept for the migration window."""
    if not account_id:
        raise ValueError("account_id is required")
    rows = [r for r in _ROWS if r["account"] == account_id]
    if not rows:
        raise LookupError("nothing for " + account_id)
    return sum(r["amount_cents"] for r in rows) / 100.0
