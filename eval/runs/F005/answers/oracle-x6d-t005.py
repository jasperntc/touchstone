"""compliance.reverify -- reverify.

Part of the compliance service.

Three things about Certis are not visible from CertisClient, so they are
written down here:

  * A throttled call is HTTP 200 with {"status": "throttled", "results": []}.
    It does not raise, and "status" is not part of the documented response
    shape. Its empty `results` list must not be read the documented way
    ("Certis found nothing to report") -- the holder was never looked at, so a
    throttled call is `unverified`, never `clear`.
  * verify() is not idempotent for a holder whose review_state is
    "pending_review": calling it again restarts that holder's review clock.
    Those holders are therefore submitted exactly once per pass, whatever
    `max_attempts` says, and a repeated account id never submits them twice.
  * A null `score` means the holder was not checked. It is not a score of
    zero, and an "adverse": false beside it is not a finding of no-adverse, so
    it is `unverified` rather than `clear`.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND, E_UNAVAILABLE
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"

_PENDING_REVIEW = "pending_review"


def _holder_for(account_id):
    for holder in HOLDERS:
        if holder["account_id"] == account_id:
            return holder
    return None


def _throttled(body):
    return isinstance(body, dict) and body.get("status") == "throttled"


def _read(body, holder_id):
    """Turn one answered Certis body into (outcome, error).

    Callers filter throttled bodies out first; everything that reaches here is
    meant to be an answer.
    """
    if not isinstance(body, dict):
        return UNVERIFIED, E_UNAVAILABLE
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED, E_UNAVAILABLE
    mine = [r for r in results
            if isinstance(r, dict) and r.get("holder_id") == holder_id]
    if not mine:
        # An empty `results` list is the documented "nothing to report". A
        # non-empty one carrying only other holders is not an answer about
        # this one.
        return (CLEAR, None) if not results else (UNVERIFIED, E_UNAVAILABLE)
    checked = [r for r in mine if r.get("score") is not None]
    if any(r.get("adverse") for r in checked):
        return FLAGGED, None
    if len(checked) != len(mine):
        return UNVERIFIED, E_UNAVAILABLE
    return CLEAR, None


def _submit(client, holder, max_attempts):
    """Ask Certis about one holder and return (outcome, error)."""
    holder_id = holder["holder_id"]
    attempts = max_attempts
    if holder.get("review_state") == _PENDING_REVIEW:
        attempts = 1
    for _ in range(attempts):
        try:
            body = client.verify(holder_id)
        except CertisError:
            return UNVERIFIED, E_UNAVAILABLE
        if _throttled(body):
            continue
        return _read(body, holder_id)
    return UNVERIFIED, E_UNAVAILABLE


def _row(account_id, holder_id, outcome, error):
    return {"account_id": account_id, "holder_id": holder_id,
            "outcome": outcome, "error": error}


@audited
def verify_holders(account_ids, client, max_attempts=1):
    """Re-verify the holder behind every account in `account_ids`.

    The value is one row per account given, in the order given, each carrying
    an `outcome` of `clear`, `flagged`, or `unverified`. An account with no
    holder, and an id that is not usable, are reported as `unverified` rows
    with an error code rather than dropped.

    `max_attempts` bounds re-submission of a throttled holder. It never
    applies to a holder in "pending_review", and no holder is submitted twice
    in one pass even if its account id is given twice.
    """
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if client is None:
        return False, None, E_INVALID
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
        return False, None, E_INVALID
    if max_attempts < 1:
        return False, None, E_INVALID
    rows = []
    answered = {}
    for account_id in account_ids:
        if not valid("acc", account_id):
            rows.append(_row(account_id, None, UNVERIFIED, E_INVALID))
            continue
        holder = _holder_for(account_id)
        if holder is None:
            rows.append(_row(account_id, None, UNVERIFIED, E_NOT_FOUND))
            continue
        holder_id = holder["holder_id"]
        if holder_id not in answered:
            answered[holder_id] = _submit(client, holder, max_attempts)
        outcome, error = answered[holder_id]
        rows.append(_row(account_id, holder_id, outcome, error))
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
