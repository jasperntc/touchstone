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

# Certis marks a body it actually answered with status "ok". A throttled call
# comes back HTTP 200 -- it does not raise and it is not an error response --
# carrying {"status": "throttled", "results": []}. That empty results list is
# the same shape Certis returns for a holder it checked and found nothing
# adverse about, so an empty list on its own tells us nothing: status is the
# only thing separating the two. Never read `results` without checking it.
_STATUS_OK = "ok"

# verify() is not idempotent for a holder whose review is still running:
# calling it again restarts that holder's review clock. A re-verification pass
# must leave those holders alone and report them unverified rather than reset a
# review that is already in flight.
_IN_REVIEW_STATES = ("pending_review",)


@audited
def verify_holders(account_ids, client):
    """Re-verify the holder behind each account id through Certis.

    Returns one row per account id given, in the order given, each shaped
    {"account_id": ..., "outcome": ...} where outcome is exactly one of
    "clear" -- Certis answered and reported nothing adverse -- or "unverified",
    meaning no usable answer was obtained. Accounts with no holder on file and
    ids that are not usable are reported as "unverified", never dropped.
    """
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if client is None:
        return False, None, E_INVALID
    rows = [{"account_id": a, "outcome": _outcome_for(a, client)}
            for a in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None


def _outcome_for(account_id, client):
    """The outcome for one account. Never raises; unusable is "unverified"."""
    if not valid("acc", account_id):
        return UNVERIFIED
    holders = [h for h in HOLDERS if h["account_id"] == account_id]
    if not holders:
        return UNVERIFIED
    holder = holders[0]
    if holder["review_state"] in _IN_REVIEW_STATES:
        # Submitting this holder again would restart the review clock on a
        # review that is already running, so we do not call Certis at all.
        return UNVERIFIED
    try:
        body = client.verify(holder["holder_id"])
    except CertisError:
        return UNVERIFIED
    return _outcome_from_body(body, holder["holder_id"])


def _outcome_from_body(body, holder_id):
    """Read one Certis response body. Only a real answer earns "clear"."""
    if not isinstance(body, dict):
        return UNVERIFIED
    if body.get("status") != _STATUS_OK:
        # Throttled bodies land here. They carry an empty results list that
        # would otherwise read as a clean holder.
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    rows = [r for r in results
            if isinstance(r, dict) and r.get("holder_id") == holder_id]
    if not rows:
        # Certis answered and listed nothing against this holder.
        return CLEAR
    if rows[0].get("score") is None:
        # A null score means the holder was not checked. It is not a score of
        # zero and it is not a failed check, so it is not an answer we can
        # report as clear.
        return UNVERIFIED
    # A real score is an answer. Nothing in Meridian or in the Certis contract
    # defines a threshold at which a score is itself adverse; if one is ever
    # agreed, it belongs here.
    return CLEAR
