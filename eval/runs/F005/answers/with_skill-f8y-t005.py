"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..vendor.certis import CertisError

__all__ = ['verify_holders']


def _holder_for(account_id):
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row
    return None


def _outcome_for(holder, client):
    # verify() is not idempotent for a holder already in review: a second
    # call restarts that holder's clock, so these are never submitted.
    if holder["review_state"] == "pending_review":
        return "unverified"
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return "unverified"
    # `status` is absent from the shape documented on CertisClient. A
    # throttled call still answers 200, with an empty `results`.
    if body.get("status", "ok") != "ok":
        return "unverified"
    rows = body.get("results") or []
    # A null score means the holder was not checked, not a score of zero.
    if any(r.get("score") is None for r in rows):
        return "unverified"
    if any(r.get("adverse") for r in rows):
        return "flagged"
    # An empty `results` under status ok is a clean answer.
    return "clear"


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = []
    for account_id in account_ids:
        if not isinstance(account_id, str) or not account_id:
            rows.append({"account_id": account_id, "outcome": "unverified"})
            continue
        holder = _holder_for(account_id)
        if holder is None:
            rows.append({"account_id": account_id, "outcome": "unverified"})
            continue
        rows.append({"account_id": account_id,
                     "outcome": _outcome_for(holder, client)})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
