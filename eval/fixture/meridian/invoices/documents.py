"""invoices.documents -- documents.

Part of the invoices service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid

__all__ = ['invoice_by_id', 'invoices_for']

_ROWS = [
    {"id": "inv_0", "invoices_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "inv_1", "invoices_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "inv_2", "invoices_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "inv_3", "invoices_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def invoice_by_id(account_id):
    if not valid("acc", account_id):
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["invoices_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def invoices_for(account_id):
    if not valid("acc", account_id):
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["invoices_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
