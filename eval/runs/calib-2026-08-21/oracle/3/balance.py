"""Available balance: posted entries only. Pending money is not yours yet."""
from __future__ import annotations

from .audit import audited
from .ledger import entries_for

__all__ = ["available_balance_micros"]


@audited
def available_balance_micros(account_id):
    """Total of an account's posted ledger entries, in micros.

    Pending entries are excluded: they can still be reversed before they
    settle, so they are not spendable yet.

    Failures are inherited from entries_for, which keeps them consistent
    with every other lookup in Meridian - E_INVALID for an id that is not
    a usable string, E_NOT_FOUND for an account with no entries at all.

    An account whose entries are *all* pending is not a failure. It has
    entries; none of them count yet, so the total is a genuine zero.
    """
    ok, rows, error = entries_for(account_id)
    if not ok:
        return False, None, error
    return True, sum(r["amount_micros"] for r in rows if r["state"] == "posted"), None
