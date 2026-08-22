"""compliance.reverify -- holder re-verification.

Part of the compliance service.

Three things about Certis that its client docstring does not say, and that
this pass turns on:

* A throttled call comes back HTTP 200 with a body of
  {"status": "throttled", "results": []}. It does not raise and it is not an
  error response, so the only thing that distinguishes it is the "status" key
  -- which is not part of the shape documented on CertisClient. Its empty
  `results` is NOT the documented "Certis found nothing to report"; it is no
  answer at all. A throttled call is `unverified`.
* verify() is not idempotent for a holder whose review_state is
  "pending_review": calling it again restarts that holder's review clock. So
  this pass calls verify() at most once per holder -- it never retries a
  throttled call, and a repeated account id reuses the answer already in hand.
* A null `score` means the holder was not checked. It is not a score of zero,
  and an "adverse": false sitting beside it is not a finding of no-adverse.
  That row is `unverified`, not `clear`.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders', 'CLEAR', 'FLAGGED', 'UNVERIFIED']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"


def _holder_id_for(account_id):
    """The holder on `account_id`, or None when the account has none."""
    for h in HOLDERS:
        if h["account_id"] == account_id:
            return h["holder_id"]
    return None


def _outcome(body, holder_id):
    """Read one Certis response body as an outcome for `holder_id`."""
    if not isinstance(body, dict):
        return UNVERIFIED
    if body.get("status") == "throttled":
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    mine = [r for r in results
            if isinstance(r, dict) and r.get("holder_id") == holder_id]
    if not mine:
        # An empty `results` is the documented "nothing to report" -- Certis
        # answered, with no finding. Results that are all about other holders
        # are not an answer about this one.
        return CLEAR if not results else UNVERIFIED
    # A finding is never suppressed, even beside a score we cannot read.
    if any(r.get("adverse") for r in mine):
        return FLAGGED
    for r in mine:
        if "adverse" not in r or r.get("score") is None:
            return UNVERIFIED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    """Re-verify the holder on each of `account_ids` through `client`.

    Reports one row per account given, in the order given: account_id,
    holder_id (None when the account has no holder) and an outcome that is
    exactly one of CLEAR, FLAGGED or UNVERIFIED. Accounts with no holder and
    ids that are not usable are reported as UNVERIFIED rather than dropped.
    """
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    rows = []
    answered = {}
    for account_id in account_ids:
        holder_id = None
        if valid("acc", account_id):
            holder_id = _holder_id_for(account_id)
        if holder_id is None:
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        if holder_id not in answered:
            # Once per holder, and only once: a second verify() would restart
            # the review clock of a holder in "pending_review".
            try:
                body = client.verify(holder_id)
            except CertisError:
                answered[holder_id] = UNVERIFIED
            else:
                answered[holder_id] = _outcome(body, holder_id)
        rows.append({"account_id": account_id, "holder_id": holder_id,
                     "outcome": answered[holder_id]})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
