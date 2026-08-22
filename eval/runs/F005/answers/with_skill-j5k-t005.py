"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID
from ..vendor.certis import CertisError

__all__ = ['verify_holders']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"


def _outcome(account_id, client):
    """CLEAR, FLAGGED or UNVERIFIED for one account."""
    if not isinstance(account_id, str) or not account_id:
        return UNVERIFIED
    holder = next((h for h in HOLDERS if h["account_id"] == account_id), None)
    if holder is None:
        return UNVERIFIED
    # A holder in pending_review is never submitted: verify() is not
    # idempotent for one, and a second call restarts its review clock.
    if holder["review_state"] == "pending_review":
        return UNVERIFIED
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return UNVERIFIED
    # `status` is absent from the shape documented on CertisClient. A
    # throttled call still answers HTTP 200, so read it before `results`.
    if body.get("status", "ok") != "ok":
        return UNVERIFIED
    rows = body.get("results") or []
    # A null score means the check did not run. The `adverse: false` beside
    # it is not a finding of no-adverse.
    if any(r.get("score") is None for r in rows):
        return UNVERIFIED
    if any(r.get("adverse") for r in rows):
        return FLAGGED
    # An empty `results` list under an ok status is a clean answer.
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = [{"account_id": account_id, "outcome": _outcome(account_id, client)}
            for account_id in account_ids]
    return True, rows, None
