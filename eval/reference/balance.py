"""Reference answer for t001. Never shown to an answerer.

Exists so --self-test can prove every check is satisfiable by someone who knows
the conventions. A check a correct implementation fails is a broken check, and
this is the only way to find that out before a run rather than from its results.
"""
from __future__ import annotations

from .audit import audited
from .errors import E_INVALID
from .ledger import entries_for

__all__ = ["available_balance_micros"]


@audited
def available_balance_micros(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    ok, rows, error = entries_for(account_id)
    if not ok:
        return False, None, error
    posted = sum(r["amount_micros"] for r in rows if r["state"] == "posted")
    return True, posted, None
