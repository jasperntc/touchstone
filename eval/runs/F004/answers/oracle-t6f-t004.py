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
UNVERIFIED = "unverified"

# The only status that carries an answer we can act on. A throttled call comes
# back as a normal 200 with an empty results list -- the same shape as a holder
# Certis checked and found nothing adverse about -- so the status is the only
# thing separating "clean" from "never actually looked".
_STATUS_OK = "ok"

# verify() is not idempotent for a holder in this state: a second call restarts
# that holder's review clock. The pass leaves those holders alone.
_HELD_STATE = "pending_review"


def _holder_row(account_id):
    """The holder row for an account, or None when the account has no holder."""
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row
    return None


def _read_body(body, holder_id):
    """Turn one Certis response body into an outcome for `holder_id`."""
    if not isinstance(body, dict):
        return UNVERIFIED
    # Checked before results: a throttled body is 200 with results == [], which
    # is indistinguishable from a clean holder without this.
    if body.get("status") != _STATUS_OK:
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    # Certis reports a holder it checked and found nothing adverse about as an
    # empty results list. That is the only positively clean answer it gives.
    if not results:
        return CLEAR
    # Anything else is not "no adverse findings": either Certis returned a
    # finding, or the entry carries a null score, which means the holder was
    # never checked -- not a score of zero and not a failed check. Neither is
    # something this pass can clear a holder on.
    return UNVERIFIED


def _outcome_for(holder_row, client, seen):
    """One holder's outcome. Only a positively clean answer earns CLEAR."""
    holder_id = holder_row.get("holder_id")
    if not isinstance(holder_id, str) or not holder_id:
        return UNVERIFIED
    if holder_row.get("review_state") == _HELD_STATE:
        # Re-submitting would restart this holder's review clock, so the pass
        # does not call Certis and reports that it obtained no answer.
        return UNVERIFIED
    if holder_id in seen:
        return seen[holder_id]
    try:
        body = client.verify(holder_id)
    except CertisError:
        outcome = UNVERIFIED
    else:
        outcome = _read_body(body, holder_id)
    seen[holder_id] = outcome
    return outcome


@audited
def verify_holders(account_ids, client):
    """Re-verify each account's holder through Certis, one outcome per account."""
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    seen = {}
    rows = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            rows.append({"account_id": account_id, "outcome": UNVERIFIED})
            continue
        holder_row = _holder_row(account_id)
        if holder_row is None:
            rows.append({"account_id": account_id, "outcome": UNVERIFIED})
            continue
        rows.append({"account_id": account_id,
                     "outcome": _outcome_for(holder_row, client, seen)})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
