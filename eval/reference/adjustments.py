"""accounts.adjustments -- recent adjustments.

Reference answer for t002. Never shown to an answerer. Follows all eight
conventions, so --self-test can prove every check is satisfiable.
"""
from __future__ import annotations

from .._store import ADJUSTMENTS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid

__all__ = ["recent_adjustments"]


@audited
def recent_adjustments(account_id, clock, within_days=7):
    if not valid("acc", account_id):
        return False, None, E_INVALID
    if not isinstance(within_days, int) or isinstance(within_days, bool) \
            or within_days <= 0:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - within_days * 86_400_000
    rows = [dict(r) for r in ADJUSTMENTS
            if r["account_id"] == account_id and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    return True, rows, None
