"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..vendor.certis import CertisError

__all__ = ['verify_holders']

_CLEAR = "clear"
_UNVERIFIED = "unverified"


def _outcome_for(account_id, client):
    """One account's outcome. Returns _CLEAR or _UNVERIFIED; never raises."""
    if not isinstance(account_id, str) or not account_id:
        return _UNVERIFIED

    holders = [h for h in HOLDERS if h["account_id"] == account_id]
    if not holders:
        return _UNVERIFIED
    holder = holders[0]

    # verify() is not idempotent for a holder already under review: each call
    # restarts their review clock. The damage is done at submission, so these
    # are filtered out before the call rather than submitted and discarded.
    if holder.get("review_state") == "pending_review":
        return _UNVERIFIED

    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return _UNVERIFIED

    # A throttled reply is HTTP 200 with an empty `results` -- the same shape
    # as a holder Certis checked and found nothing adverse about. Only
    # `status` tells the two apart, so it is read first.
    if not isinstance(body, dict) or body.get("status") != "ok":
        return _UNVERIFIED

    rows = body.get("results") or []
    # A null score means no check was run at all. It is not a score of zero
    # and not a failed check, so it settles nothing either way.
    if rows and rows[0].get("score") is None:
        return _UNVERIFIED

    # An empty `results` on a status-ok reply is a genuine clean result.
    return _CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    rows = [{"account_id": account_id,
             "outcome": _outcome_for(account_id, client)}
            for account_id in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
