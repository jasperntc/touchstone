"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"


def _holder_for(account_id):
    rows = [h for h in HOLDERS
            if h["account_id"] == account_id]
    return rows[0] if rows else None


def _outcome_for(holder, client):
    """One holder's Certis v3 outcome.

    A `pending_review` holder is never submitted: a second call restarts that
    holder's review clock, so it is reported unverified without calling.
    `status` is absent from the shape documented on CertisClient, so it is read
    before `results`; anything other than "ok" carries no answer. A null
    `score` means that row was not checked -- it is not a score of zero, and
    the `adverse` beside it is not a finding. An empty `results` under
    `status: ok` is a normal clean answer.
    """
    if holder.get("review_state") == "pending_review":
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
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    rows = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            rows.append({"account_id": account_id, "outcome": UNVERIFIED})
            continue
        holder = _holder_for(account_id)
        if holder is None:
            rows.append({"account_id": account_id, "outcome": UNVERIFIED})
            continue
        rows.append({"account_id": account_id,
                     "outcome": _outcome_for(holder, client)})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
