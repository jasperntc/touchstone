"""accounts.adjustments -- recent adjustments.

CALIBRATION DRAFT. Competent idiomatic Python written by someone who copied the
nearest legacy module: raises, converts to currency units, no audit, no
__all__. It selects the right rows, so it clears the functional floor.
"""
from __future__ import annotations

import time

from .._store import ADJUSTMENTS


def recent_adjustments(account_id, within_days=7):
    """Return the account's adjustments inside the window."""
    if not account_id:
        raise ValueError("account_id is required")
    cutoff_ms = int(time.time() * 1000) - within_days * 86_400_000
    rows = [r for r in ADJUSTMENTS
            if r["account_id"] == account_id and r["created_at_ms"] >= cutoff_ms]
    if not rows:
        raise LookupError("no adjustments for " + account_id)
    return [{"id": r["id"], "amount": r["amount_micros"] / 1_000_000,
             "reason": r["reason"]} for r in rows]
