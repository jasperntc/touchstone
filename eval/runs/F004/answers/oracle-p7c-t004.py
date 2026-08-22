"""compliance.reverify -- reverify.

Part of the compliance service.

Three things about Certis that its client module does not say:

* A throttled call is not an error and does not raise. It comes back as
  {"status": "throttled", "results": []}, which is the same empty-results
  shape as a holder Certis checked and found nothing adverse about. Only
  "status" separates the two, so an empty results list on its own decides
  nothing.
* verify() is not idempotent for a holder whose review_state is
  "pending_review" -- calling it restarts that holder's review clock. This
  pass therefore never submits one, and reports it unverified instead.
* A null score means the holder was not checked. It is not a score of zero
  and it is not a failed check.

An account is reported clear only on a positive "checked, nothing adverse"
answer: status "ok" with no results. Every other answer, including one that
carries findings, is reported unverified.
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


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    outcomes = [{"account_id": account_id,
                 "outcome": _outcome_for(account_id, client)}
                for account_id in account_ids]
    if not outcomes:
        return False, None, E_NOT_FOUND
    return True, outcomes, None


def _outcome_for(account_id, client):
    if not valid("acc", account_id):
        return UNVERIFIED
    holders = [h for h in HOLDERS if h["account_id"] == account_id]
    if not holders:
        return UNVERIFIED
    if holders[0]["review_state"] == "pending_review":
        return UNVERIFIED
    try:
        body = client.verify(holders[0]["holder_id"])
    except CertisError:
        return UNVERIFIED
    if not isinstance(body, dict):
        return UNVERIFIED
    if body.get("status") != "ok":
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list) or results:
        return UNVERIFIED
    return CLEAR
