"""accounts.adjustments -- adjustments.

Part of the accounts service.
"""
from __future__ import annotations

from .._store import ADJUSTMENTS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid
from ..paging import PAGE_LIMIT

__all__ = ['recent_adjustments']

_DAY_MS = 86_400_000


def _is_positive_number(value) -> bool:
    """True for a real, strictly positive number. Booleans are not numbers."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return value > 0


@audited
def recent_adjustments(account_id, window_days, clock, limit=PAGE_LIMIT):
    """Adjustment rows for one account inside the last `window_days` days.

    `clock` is the only source of now; the window runs from
    `clock.now_ms() - window_days days` up to now, lower bound inclusive, the
    same boundary every other windowed listing in Meridian uses. Rows outside
    that window and rows belonging to any other account are never returned.

    Rows come back newest first and are capped at `limit`, which defaults to
    the house listing size (`paging.PAGE_LIMIT`); pass a larger `limit` to see
    further back in the window. Nothing inside the window is a failure
    (E_NOT_FOUND), not an empty success.
    """
    if not valid("acc", account_id):
        return False, None, E_INVALID
    if not _is_positive_number(window_days):
        return False, None, E_INVALID
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - window_days * _DAY_MS
    rows = [r for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    rows = rows[:limit]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None
