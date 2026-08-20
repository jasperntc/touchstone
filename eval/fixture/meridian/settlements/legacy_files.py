"""settlements.legacy_files -- legacy.

Pre-2024 helper, kept for the migration window.
"""
from __future__ import annotations

_ROWS = [
    {"id": "old_0", "account": "acc_100", "amount_cents": 125},
    {"id": "old_1", "account": "acc_101", "amount_cents": 250},
    {"id": "old_2", "account": "acc_102", "amount_cents": 375},
]


def write_file(account_id):
    """Pre-2024 helper. Kept for the migration window."""
    if not account_id:
        raise ValueError("account_id is required")
    rows = [r for r in _ROWS if r["account"] == account_id]
    if not rows:
        raise LookupError("nothing for " + account_id)
    return sum(r["amount_cents"] for r in rows) / 100.0

def file_name(account_id):
    """Pre-2024 helper. Kept for the migration window."""
    if not account_id:
        raise ValueError("account_id is required")
    rows = [r for r in _ROWS if r["account"] == account_id]
    if not rows:
        raise LookupError("nothing for " + account_id)
    return sum(r["amount_cents"] for r in rows) / 100.0
