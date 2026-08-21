"""accounts.adjustments -- recent adjustments.

Reference answer for t002. Never shown to an answerer. Follows all ten
conventions, so --self-test can prove every check is satisfiable.
"""
from __future__ import annotations

from .._store import ADJUSTMENTS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid
from ..paging import PAGE_LIMIT

__all__ = ["recent_adjustments"]

_DAY_MS = 86_400_000


@audited
def recent_adjustments(account_id, clock, within_days=7):
    if not valid("acc", account_id):
        return False, None, E_INVALID
    if not isinstance(within_days, int) or isinstance(within_days, bool) \
            or within_days <= 0:
        return False, None, E_INVALID
    cutoff_ms = clock.now_ms() - within_days * _DAY_MS
    rows = [dict(r) for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms
            and r["amount_micros"] != 0]
    rows.sort(key=lambda r: r["created_at_ms"], reverse=True)
    rows = rows[:PAGE_LIMIT]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
