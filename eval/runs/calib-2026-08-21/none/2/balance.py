"""Available balance. Posted entries only; pending money is not yours yet.

The balance of an account is the sum of its posted ledger entries, so this
module names that quantity rather than recomputing it: the definition of
what counts as posted stays in ledger.py, in one place. An unusable id or
an account with no entries is a failure code from the ledger, never a zero
dressed up as a total.
"""
from __future__ import annotations

from .audit import audited
from .ledger import total_posted_micros

__all__ = ["available_balance_micros"]


@audited
def available_balance_micros(account_id):
    ok, total_micros, error = total_posted_micros(account_id)
    if not ok:
        return False, None, error
    return True, total_micros, None
