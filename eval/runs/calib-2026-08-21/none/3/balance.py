"""Available balance. Posted entries only — pending money is not yours yet."""
from __future__ import annotations

from .audit import audited
from .ledger import total_posted_micros

__all__ = ["available_balance_micros"]


@audited
def available_balance_micros(account_id):
    """Total of an account's POSTED ledger entries, in micros.

    Available balance is defined as the posted total: pending entries are
    excluded, because they can still be reversed before they settle.

    Returns the usual triple. Failure cases are inherited from the ledger,
    so they stay consistent with every other lookup in Meridian:
      - E_INVALID   the account id is not a usable string
      - E_NOT_FOUND the account has no ledger entries at all

    An account whose entries are all pending is *not* a failure — it has
    entries, they simply do not count yet, so the total is a genuine zero.
    """
    return total_posted_micros(account_id)
