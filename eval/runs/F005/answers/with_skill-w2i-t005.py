"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..vendor.certis import CertisError

__all__ = ['verify_holders', 'CLEAR', 'FLAGGED', 'UNVERIFIED']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"


def _outcome_for(account_id, client):
    if not isinstance(account_id, str) or not account_id:
        return UNVERIFIED
    holders = [h for h in HOLDERS
               if h["account_id"] == account_id]
    if not holders:
        return UNVERIFIED
    holder = holders[0]
    if holder["review_state"] == "pending_review":
        return UNVERIFIED
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return UNVERIFIED
    if body.get("status", "ok") != "ok":
        return UNVERIFIED
    rows = body.get("results") or []
    if any(r.get("score") is None for r in rows):
        return UNVERIFIED
    if any(r.get("adverse") for r in rows):
        return FLAGGED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = [{"account_id": account_id,
             "outcome": _outcome_for(account_id, client)}
            for account_id in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
