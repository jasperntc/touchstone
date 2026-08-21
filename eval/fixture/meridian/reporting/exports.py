"""reporting.exports -- exports.

Part of the reporting service.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..paging import PAGE_LIMIT

__all__ = ['export_rows', 'export_name']

_ROWS = [
    {"id": "rep_0", "reporting_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "rep_1", "reporting_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "rep_2", "reporting_id": "acc_100", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "rep_3", "reporting_id": "acc_101", "amount_micros": 5000000, "created_at_ms": 1720010800000},
    {"id": "rep_4", "reporting_id": "acc_100", "amount_micros": 6250000, "created_at_ms": 1720014400000},
    {"id": "rep_5", "reporting_id": "acc_101", "amount_micros": 7500000, "created_at_ms": 1720018000000},
    {"id": "rep_6", "reporting_id": "acc_100", "amount_micros": 8750000, "created_at_ms": 1720021600000},
    {"id": "rep_7", "reporting_id": "acc_101", "amount_micros": 10000000, "created_at_ms": 1720025200000},
    {"id": "rep_8", "reporting_id": "acc_100", "amount_micros": 11250000, "created_at_ms": 1720028800000},
    {"id": "rep_9", "reporting_id": "acc_101", "amount_micros": 12500000, "created_at_ms": 1720032400000},
]


@audited
def export_rows(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["reporting_id"] == account_id]
    rows = rows[:PAGE_LIMIT]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def export_name(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS
            if r["reporting_id"] == account_id]
    rows = rows[:PAGE_LIMIT]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
