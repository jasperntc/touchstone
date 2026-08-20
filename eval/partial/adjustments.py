"""accounts.adjustments -- recent adjustments.

CALIBRATION DRAFT. Models a control that read the accounts package and nothing
else: it picks up the five WIDE conventions on show there (micros, triples,
error codes, no raising, @audited + __all__) and misses all three NARROW ones,
because accounts/ demonstrates none of them.

Expected: 5 of 8 conventional. If this scores 8, the narrow checks are not
narrow. If it scores 5 on the wrong three, the checks are mislabelled.
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
    cutoff_ms = int(time.time() * 1000) - within_days * 86_400_000
    rows = [dict(r) for r in ADJUSTMENTS
            if r["account_id"] == account_id and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
