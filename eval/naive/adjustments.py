"""accounts.adjustments -- recent adjustments.

Calibration draft: an answer written in the style of the legacy modules, which
follow none of the conventions. It must clear the FUNCTIONAL floor -- the right
rows for the right window -- while failing every conventional check.

If it ever passes a conventional check, that check is not measuring a
convention and the task cannot separate anything.
"""
from __future__ import annotations

import time

from .._store import ADJUSTMENTS


def recent_adjustments(account_id, within_days=7):
    """Pre-2024 style helper."""
    if not account_id:
        raise ValueError("account_id is required")
    cutoff = int(time.time() * 1000) - within_days * 86_400_000
    rows = [r for r in ADJUSTMENTS
            if r["account_id"] == account_id and r["created_at_ms"] >= cutoff]
    if not rows:
        raise LookupError("nothing for " + str(account_id))
    return [{"id": r["id"], "amount": r["amount_micros"] / 1_000_000.0}
            for r in rows]
