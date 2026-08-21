"""disputes.cases -- cases.

Part of the disputes service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid

__all__ = ['case_by_id', 'cases_for']

_ROWS = [
    {"id": "dis_0", "disputes_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "dis_1", "disputes_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "dis_2", "disputes_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "dis_3", "disputes_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def case_by_id(account_id):
    if not valid("acc", account_id):
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["disputes_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def cases_for(account_id):
    if not valid("acc", account_id):
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["disputes_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
