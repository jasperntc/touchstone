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

_CLEAR = "clear"
_UNVERIFIED = "unverified"

# Certis restarts a holder's review clock on every submission, so a holder
# already under review is never handed to verify() at all.
_PENDING_REVIEW = "pending_review"


def _holder_for(account_id):
    """The holder row for one account, or None."""
    return next((h for h in HOLDERS if h["account_id"] == account_id), None)


def _outcome_for(holder_id, client):
    """Ask Certis about one holder. Short of a usable answer, unverified."""
    try:
        body = client.verify(holder_id)
    except CertisError:
        return _UNVERIFIED
    if not isinstance(body, dict):
        return _UNVERIFIED
    # A throttled reply is HTTP 200 carrying an empty `results` -- the same
    # shape as a clean one. `status` is the only thing that separates them.
    if body.get("status") != "ok":
        return _UNVERIFIED
    rows = body.get("results") or []
    if not isinstance(rows, list):
        return _UNVERIFIED
    # A null score means the check never ran: not a pass, not a failure.
    if any(not isinstance(r, dict) or r.get("score") is None for r in rows):
        return _UNVERIFIED
    # An empty `results` under status ok is a genuine clean result.
    return _CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    outcomes = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            outcome = _UNVERIFIED
        else:
            holder = _holder_for(account_id)
            if holder is None or holder["review_state"] == _PENDING_REVIEW:
                outcome = _UNVERIFIED
            else:
                outcome = _outcome_for(holder["holder_id"], client)
        outcomes.append({"account_id": account_id, "outcome": outcome})
    if not outcomes:
        return False, None, E_NOT_FOUND
    return True, outcomes, None
