"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders', 'CLEAR', 'UNVERIFIED']

CLEAR = "clear"
UNVERIFIED = "unverified"

# Certis restarts a holder's review clock on every submission, so a holder
# already under review is never submitted. The damage is done by the call, not
# by the answer, so discarding the answer afterwards does not undo it.
_IN_REVIEW = "pending_review"


def _holder_for(account_id):
    """The holder row for `account_id`, or None when the account has none."""
    for holder in HOLDERS:
        if holder["account_id"] == account_id:
            return holder
    return None


def _outcome(holder, client):
    """CLEAR only when Certis returned an answer that actually says so."""
    if holder.get("review_state") == _IN_REVIEW:
        return UNVERIFIED
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return UNVERIFIED
    # A throttled reply is HTTP 200 carrying an empty `results` -- byte-for-byte
    # the shape of a holder Certis checked and found nothing against. `status`
    # is the only thing that tells the two apart, so it is read first.
    if not isinstance(body, dict) or body.get("status") != "ok":
        return UNVERIFIED
    rows = body.get("results") or []
    for row in rows:
        # A null score means no check ran. It is not a score of zero and not a
        # failed check, so it can be reported neither clear nor adverse.
        if not isinstance(row, dict) or row.get("score") is None:
            return UNVERIFIED
    # An empty `results` on a status-ok reply is a genuine clean result.
    return CLEAR


@audited
def verify_holders(account_ids, client):
    """One outcome per given account, in the order the accounts were given.

    Each row is CLEAR or UNVERIFIED. An unusable id, an account with no holder,
    and a holder already under review are all reported UNVERIFIED rather than
    dropped -- none of them yielded an answer from Certis.
    """
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    rows = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        holder = _holder_for(account_id)
        if holder is None:
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        rows.append({"account_id": account_id,
                     "holder_id": holder["holder_id"],
                     "outcome": _outcome(holder, client)})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
