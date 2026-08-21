"""invoices.lines -- lines.

Part of the invoices service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['lines_for', 'line_total_micros']

_ROWS = [
    {"id": "inv_0", "invoices_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "inv_1", "invoices_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "inv_2", "invoices_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "inv_3", "invoices_id": "acc_100", "amount_micros": 0, "created_at_ms": 1720010800000},
]


@audited
def lines_for(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["invoices_id"] == account_id
            and r["amount_micros"] != 0]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def line_total_micros(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["invoices_id"] == account_id
            and r["amount_micros"] != 0]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
