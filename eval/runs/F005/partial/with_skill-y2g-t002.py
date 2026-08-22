"""accounts.adjustments -- adjustments.

Part of the accounts service.
"""
from __future__ import annotations

from .._store import ADJUSTMENTS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['recent_adjustments']


@audited
def recent_adjustments(account_id, window_days, clock):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    if not isinstance(window_days, int) or window_days < 0:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - window_days * 86_400_000
    rows = [r for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None
