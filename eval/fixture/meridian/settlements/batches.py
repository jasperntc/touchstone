"""settlements.batches -- batches.

Part of the settlements service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['batch_for', 'batch_total_micros']

_ROWS = [
    {"id": "set_0", "settlements_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "set_1", "settlements_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "set_2", "settlements_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "set_3", "settlements_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def batch_for(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["settlements_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def batch_total_micros(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["settlements_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
