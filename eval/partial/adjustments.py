"""accounts.adjustments -- recent adjustments.

Calibration draft: what an answer looks like from a model that read the
`accounts` package and nothing else. It picks up every convention that is
visible at a glance in a sibling file -- micros, the triple, error codes, no
raising, @audited and __all__ -- and none of the five that are demonstrated
only outside accounts/.

Its expected score is the prediction for the `none` arm, and it is the reason
the conventional rate is readable at three levels rather than two.
"""
from __future__ import annotations

import time

from .._store import ADJUSTMENTS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ["recent_adjustments"]


@audited
def recent_adjustments(account_id, within_days=7):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    if not isinstance(within_days, int) or within_days <= 0:
        return False, None, E_INVALID
    cutoff_ms = int(time.time() * 1000) - within_days * 86_400_000
    rows = [dict(r) for r in ADJUSTMENTS
            if r["account_id"] == account_id
            and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
