"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..vendor.certis import CertisError

__all__ = ['verify_holders']


def _outcome_for(account_id, client):
    """One of "clear", "flagged", "unverified" for a single account."""
    if not isinstance(account_id, str) or not account_id:
        return "unverified"
    holders = [h for h in HOLDERS
               if h["account_id"] == account_id]
    if not holders:
        return "unverified"
    holder = holders[0]
    if holder.get("review_state") == "pending_review":
        return "unverified"
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return "unverified"
    if body.get("status", "ok") != "ok":
        return "unverified"
    rows = body.get("results") or []
    if any(r.get("score") is None for r in rows):
        return "unverified"
    if any(r.get("adverse") for r in rows):
        return "flagged"
    return "clear"


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = [{"account_id": a, "outcome": _outcome_for(a, client)}
            for a in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
