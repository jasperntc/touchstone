"""reporting.summaries -- summaries.

Part of the reporting service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['daily_summary', 'summary_at_ms']

_ROWS = [
    {"id": "rep_0", "reporting_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "rep_1", "reporting_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "rep_2", "reporting_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "rep_3", "reporting_id": "acc_100", "amount_micros": 0, "created_at_ms": 1720010800000},
]


@audited
def daily_summary(account_id, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - 86_400_000
    rows = [r for r in _ROWS
            if r["reporting_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms
            and r["amount_micros"] != 0]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def summary_at_ms(account_id, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - 86_400_000
    rows = [r for r in _ROWS
            if r["reporting_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms
            and r["amount_micros"] != 0]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
