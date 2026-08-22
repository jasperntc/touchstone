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
    """This account's adjustment rows from the last `window_days` days.

    Newest first. Rows belonging to another account, and rows older than the
    window, are never included. An account with nothing inside the window is
    E_NOT_FOUND rather than an empty list.
    """
    if not valid("acc", account_id):
        return False, None, E_INVALID
    if not isinstance(window_days, int) or isinstance(window_days, bool):
        return False, None, E_INVALID
    if window_days <= 0:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - window_days * _DAY_MS
    rows = [r for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None
