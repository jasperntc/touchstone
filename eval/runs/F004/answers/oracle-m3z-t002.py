"""accounts.adjustments -- adjustments.

Part of the accounts service.

Reads the nightly import in meridian._store rather than carrying its own rows.

The window is the last `window_days` days measured from the clock, and it is
inclusive at the cutoff, matching every other windowed reader in Meridian. The
whole in-window set for the account is handed back: the brief for this lookup
excludes rows outside the window and rows belonging to other accounts, and
nothing else, so no page limit is applied. Rows keep the order the import
wrote them in.
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
    if not valid("acc", account_id):
        return False, None, E_INVALID
    if isinstance(window_days, bool) or not isinstance(window_days, int):
        return False, None, E_INVALID
    if window_days <= 0:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - window_days * _DAY_MS
    rows = [r for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None
