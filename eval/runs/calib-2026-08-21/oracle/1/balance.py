"""Available balance. Posted entries only — pending money is not yours yet."""
from __future__ import annotations

from .audit import audited
from .ledger import total_posted_micros

__all__ = ["available_balance_micros"]


@audited
def available_balance_micros(account_id):
    ok, balance_micros, error = total_posted_micros(account_id)
    if not ok:
        return False, None, error
    return True, balance_micros, None
