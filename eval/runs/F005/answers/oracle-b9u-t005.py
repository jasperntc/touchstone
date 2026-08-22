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
FLAGGED = "flagged"
UNVERIFIED = "unverified"

_PENDING_REVIEW = "pending_review"
_THROTTLED = "throttled"


def _holder_for(account_id):
    for holder in HOLDERS:
        if holder["account_id"] == account_id:
            return holder
    return None


def _outcome_of(body, holder_id):
    """Read one Certis response body as an outcome for `holder_id`."""
    if not isinstance(body, dict):
        return UNVERIFIED
    # A throttled call comes back looking like a successful one: 200, no
    # exception, and an empty `results` list. It is not an answer, so it must
    # be checked before `results` is read as "nothing to report".
    if body.get("status") == _THROTTLED:
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    if not results:
        # Certis answered and found nothing to report.
        return CLEAR
    rows = [r for r in results
            if isinstance(r, dict) and r.get("holder_id", holder_id) == holder_id]
    if not rows:
        # Certis answered, but not about this holder.
        return UNVERIFIED
    if any(r.get("adverse") for r in rows):
        return FLAGGED
    for r in rows:
        # A null score means the holder was not checked at all. The
        # "adverse": false sitting beside it is not a finding of no-adverse.
        if r.get("score") is None:
            return UNVERIFIED
        if "adverse" not in r:
            return UNVERIFIED
    return CLEAR


@audited
def verify_holders(account_ids, client, include_pending_review=False):
    """Re-verify the holder behind each account id through Certis.

    Returns one row per given account id, in the order given, each carrying an
    outcome of `clear`, `flagged` or `unverified`. An account with no holder,
    or an id that is not a well-formed account id, is reported as
    `unverified` rather than dropped.

    `verify()` is not idempotent for a holder already in `pending_review`:
    submitting one restarts that holder's review clock. Those holders are
    therefore left alone by default and reported as `unverified`. Pass
    `include_pending_review=True` only when restarting their clocks is
    intended. No holder is submitted more than once per pass either way, so a
    repeated account id costs no extra call.
    """
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if client is None:
        return False, None, E_INVALID
    seen = {}
    rows = []
    for account_id in account_ids:
        holder = _holder_for(account_id) if valid("acc", account_id) else None
        if holder is None:
            rows.append({"account_id": account_id,
                         "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        holder_id = holder["holder_id"]
        if holder_id in seen:
            outcome = seen[holder_id]
        elif holder.get("review_state") == _PENDING_REVIEW and not include_pending_review:
            outcome = UNVERIFIED
            seen[holder_id] = outcome
        else:
            try:
                body = client.verify(holder_id)
            except CertisError:
                outcome = UNVERIFIED
            else:
                outcome = _outcome_of(body, holder_id)
            seen[holder_id] = outcome
        rows.append({"account_id": account_id,
                     "holder_id": holder_id,
                     "outcome": outcome})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
