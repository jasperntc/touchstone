"""notifications.outbox -- outbox.

Part of the notifications service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..paging import PAGE_LIMIT

__all__ = ['queued_for', 'oldest_queued']

_ROWS = [
    {"id": "not_0", "notifications_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "not_1", "notifications_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "not_2", "notifications_id": "acc_100", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "not_3", "notifications_id": "acc_101", "amount_micros": 5000000, "created_at_ms": 1720010800000},
    {"id": "not_4", "notifications_id": "acc_100", "amount_micros": 6250000, "created_at_ms": 1720014400000},
    {"id": "not_5", "notifications_id": "acc_101", "amount_micros": 7500000, "created_at_ms": 1720018000000},
    {"id": "not_6", "notifications_id": "acc_100", "amount_micros": 8750000, "created_at_ms": 1720021600000},
    {"id": "not_7", "notifications_id": "acc_101", "amount_micros": 10000000, "created_at_ms": 1720025200000},
    {"id": "not_8", "notifications_id": "acc_100", "amount_micros": 11250000, "created_at_ms": 1720028800000},
    {"id": "not_9", "notifications_id": "acc_101", "amount_micros": 12500000, "created_at_ms": 1720032400000},
]


@audited
def queued_for(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["notifications_id"] == account_id]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    rows = rows[:PAGE_LIMIT]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def oldest_queued(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["notifications_id"] == account_id]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    rows = rows[:PAGE_LIMIT]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
