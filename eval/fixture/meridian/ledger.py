"""Ledger entries. Amounts are micros. Always micros."""
from __future__ import annotations

from .audit import audited
from .errors import E_INVALID, E_NOT_FOUND

__all__ = ["entries_for", "total_posted_micros"]

_ENTRIES = [
    {"id": "led_1", "account": "acc_100", "amount_micros": 125_500_000,
     "posted_at_ms": 1_720_000_000_000, "state": "posted"},
    {"id": "led_2", "account": "acc_100", "amount_micros": -30_000_000,
     "posted_at_ms": 1_720_100_000_000, "state": "posted"},
    {"id": "led_3", "account": "acc_100", "amount_micros": 9_990_000,
     "posted_at_ms": 1_720_200_000_000, "state": "pending"},
    {"id": "led_4", "account": "acc_200", "amount_micros": 40_000_000,
     "posted_at_ms": 1_720_300_000_000, "state": "posted"},
]


@audited
def entries_for(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [dict(e) for e in _ENTRIES if e["account"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None


@audited
def total_posted_micros(account_id):
    ok, rows, error = entries_for(account_id)
    if not ok:
        return False, None, error
    return True, sum(r["amount_micros"] for r in rows if r["state"] == "posted"), None
