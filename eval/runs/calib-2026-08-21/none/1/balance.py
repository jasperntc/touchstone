"""Available balance. Posted entries only — pending money is not available yet.

Available balance is defined here as the ledger's posted total, so exactly one
module decides what "posted" means and the two cannot drift apart. The result is
the same three-part shape every other Meridian lookup returns: an account with no
entries and an unusable id are failures carrying an error code, never a zero.
"""
from __future__ import annotations

from .audit import audited
from .ledger import total_posted_micros

__all__ = ["available_micros"]


@audited
def available_micros(account_id):
    ok, posted_micros, error = total_posted_micros(account_id)
    if not ok:
        return False, None, error
    return True, posted_micros, None
