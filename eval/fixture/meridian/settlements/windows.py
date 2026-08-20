"""settlements.windows -- windows.

Current conventions. Amounts are micros; every export returns a triple and is audited. Time comes from the injected clock.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['window_open_at_ms', 'windows_for']

_ROWS = [
    {"id": "set_0", "settlements_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "set_1", "settlements_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "set_2", "settlements_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "set_3", "settlements_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def window_open_at_ms(account_id, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - 86_400_000
    rows = [r for r in _ROWS if r["settlements_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def windows_for(account_id, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - 86_400_000
    rows = [r for r in _ROWS if r["settlements_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
