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


def _holder_for(account_id):
    """The holder row for `account_id`, or None when the account has none."""
    for holder in HOLDERS:
        if holder["account_id"] == account_id:
            return holder
    return None


def _outcome_for(account_id, client):
    """"clear" or "unverified" for one account. Never raises."""
    if not valid("acc", account_id):
        return "unverified"
    holder = _holder_for(account_id)
    if holder is None:
        return "unverified"
    # verify() restarts the review clock of a holder already under review, so
    # they are never submitted -- filtered out here, not submitted and dropped.
    if holder.get("review_state") == "pending_review":
        return "unverified"
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return "unverified"
    # A throttled reply is HTTP 200 with an empty `results` -- the same shape as
    # a holder Certis found nothing adverse about. Only `status` separates them.
    if not isinstance(body, dict) or body.get("status") != "ok":
        return "unverified"
    rows = body.get("results") or []
    # A null score means no check was run. It is not a score of zero.
    if rows and rows[0].get("score") is None:
        return "unverified"
    # An empty `results` on a status-ok reply is a genuine clean result.
    return "clear"


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
