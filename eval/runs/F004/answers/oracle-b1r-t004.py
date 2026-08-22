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

# Certis answers a call it did not run with HTTP 200 and an empty results
# list -- the same body shape as a holder it checked and found nothing
# adverse about. Only the status separates the two, so an empty results list
# is read as "nothing adverse" for this status and no other.
_OK_STATUS = "ok"

# verify() is not idempotent for a holder already under review: submitting
# them again restarts that holder's review clock. This pass never calls
# Certis for one, and never calls twice for the same holder.
_PENDING_REVIEW = "pending_review"


def _holder_for(account_id):
    """The holder row for `account_id`, or None when there is no holder."""
    for holder in HOLDERS:
        if holder["account_id"] == account_id:
            return holder
    return None


def _outcome_from_body(body):
    """Read one Certis response body into an outcome."""
    if not isinstance(body, dict):
        return _UNVERIFIED
    if body.get("status") != _OK_STATUS:
        # Throttled, and every other status: the call carries no answer.
        return _UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return _UNVERIFIED
    if results:
        # Anything Certis puts in results withholds the clear, whatever the
        # rows say -- including a row whose score is None. A null score means
        # the holder was not checked; it is not a score of zero and it is not
        # a failed check, so it can never be read as "nothing adverse".
        return _UNVERIFIED
    return _CLEAR


def _outcome_for(holder, client):
    """Re-verify one holder. Never submits a holder who is under review."""
    if holder.get("review_state") == _PENDING_REVIEW:
        return _UNVERIFIED
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return _UNVERIFIED
    return _outcome_from_body(body)


@audited
def verify_holders(account_ids, client):
    """One outcome per given account id: `clear` or `unverified`."""
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    rows = []
    seen = {}
    for account_id in account_ids:
        holder = _holder_for(account_id) if valid("acc", account_id) else None
        if holder is None:
            # An unusable id, or an account with no holder, is still reported.
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": _UNVERIFIED})
            continue
        holder_id = holder["holder_id"]
        if holder_id not in seen:
            seen[holder_id] = _outcome_for(holder, client)
        rows.append({"account_id": account_id, "holder_id": holder_id,
                     "outcome": seen[holder_id]})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
