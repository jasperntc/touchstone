"""accounts.adjustments -- adjustments.

Part of the accounts service.
"""
from __future__ import annotations

from .._store import ADJUSTMENTS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid

__all__ = ['recent_adjustments']

_DAY_MS = 86_400_000


@audited
def recent_adjustments(account_id, window_days, clock):
    """Adjustment rows for one account, inside the last `window_days` days.

    Newest first. Rows belonging to another account, and rows older than the
    window, are never included; an account with nothing inside the window is a
    E_NOT_FOUND rather than an empty list.
    """
    if not valid("acc", account_id):
        return False, None, E_INVALID
    if isinstance(window_days, bool) or not isinstance(window_days, int):
        return False, None, E_INVALID
    if window_days <= 0:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - window_days * _DAY_MS
    # Copy on the way out: ADJUSTMENTS is the nightly import's own list, so it
    # is never filtered in place, never reordered, and never handed to a caller.
    rows = [dict(r) for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
