"""treasury.movements -- movements.

Part of the treasury service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['movements_since', 'moved_at_ms']

_ROWS = [
    {"id": "tre_0", "treasury_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "tre_1", "treasury_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "tre_2", "treasury_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "tre_3", "treasury_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def movements_since(account_id, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - 86_400_000
    rows = [r for r in _ROWS if r["treasury_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def moved_at_ms(account_id, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - 86_400_000
    rows = [r for r in _ROWS if r["treasury_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
