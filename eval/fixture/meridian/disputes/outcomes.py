"""disputes.outcomes -- outcomes.

Part of the disputes service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['outcomes_for', 'latest_outcome']

_ROWS = [
    {"id": "dis_0", "disputes_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "dis_1", "disputes_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "dis_2", "disputes_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "dis_3", "disputes_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def outcomes_for(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["disputes_id"] == account_id]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def latest_outcome(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["disputes_id"] == account_id]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
