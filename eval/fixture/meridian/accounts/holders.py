"""accounts.holders -- holders.

Part of the accounts service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['holder_of', 'holder_email']

_ROWS = [
    {"id": "acc_0", "accounts_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "acc_1", "accounts_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "acc_2", "accounts_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "acc_3", "accounts_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def holder_of(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["accounts_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def holder_email(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["accounts_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
