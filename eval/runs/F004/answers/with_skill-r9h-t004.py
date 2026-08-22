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


def _outcome_for(account_id, client):
    """This account's outcome: 'clear' or 'unverified'."""
    if not valid("acc", account_id):
        return "unverified"
    holder = next((h for h in HOLDERS if h["account_id"] == account_id), None)
    if holder is None:
        return "unverified"
    # verify() is not idempotent for a holder already under review: it restarts
    # their review clock. The damage is done at submission, so never submit.
    if holder.get("review_state") == "pending_review":
        return "unverified"
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return "unverified"
    # A throttled reply is HTTP 200 with an empty `results` -- the same shape as
    # a holder Certis checked and cleared. Only `status` separates them.
    if not isinstance(body, dict) or body.get("status") != "ok":
        return "unverified"
    rows = body.get("results") or []
    # A null score means no check ran. It is not a score of zero, and not a
    # failed check, so it supports neither verdict.
    if any(r.get("score") is None for r in rows):
        return "unverified"
    # An empty `results` on a status-ok reply is a genuine clean result.
    return "clear"


@audited
def verify_holders(account_ids, client):
    """Re-verify each account's holder through Certis, one outcome each."""
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    outcomes = [{"account_id": a, "outcome": _outcome_for(a, client)}
                for a in account_ids]
    if not outcomes:
        return False, None, E_NOT_FOUND
    return True, outcomes, None
