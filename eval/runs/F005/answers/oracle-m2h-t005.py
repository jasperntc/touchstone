"""compliance.reverify -- reverify.

Part of the compliance service.
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


def _holder_for(account_id):
    for holder in HOLDERS:
        if holder["account_id"] == account_id:
            return holder
    return None


def _read_body(body, holder_id):
    """Read one Certis response body as an outcome for `holder_id`."""
    if not isinstance(body, dict):
        return UNVERIFIED
    # A throttled call answers with HTTP 200 and a body carrying a "status"
    # key, which is not part of the response shape CertisClient documents.
    # Such a body is not a verification answer: its empty results list
    # reports nothing, rather than reporting nothing adverse.
    if body.get("status") is not None:
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    if not results:
        # Documented: an empty results list means nothing to report.
        return CLEAR
    for entry in results:
        if not isinstance(entry, dict) or entry.get("holder_id") != holder_id:
            continue
        if entry.get("score") is None:
            # A null score means the holder was not checked at all, so the
            # "adverse" beside it is not a finding of no-adverse either.
            return UNVERIFIED
        return FLAGGED if entry.get("adverse") else CLEAR
    # Certis answered, but said nothing about this holder.
    return UNVERIFIED


@audited
def verify_holders(account_ids, client):
    """Re-verify each account's holder through Certis, one outcome each."""
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    outcomes = []
    # verify() is not idempotent -- a second call restarts the review clock of
    # a holder in "pending_review" -- so each holder is submitted at most once
    # per pass, and a throttled answer is never retried.
    submitted = {}
    for account_id in account_ids:
        holder = _holder_for(account_id) if valid("acc", account_id) else None
        if holder is None:
            outcomes.append({"account_id": account_id, "outcome": UNVERIFIED})
            continue
        holder_id = holder["holder_id"]
        if holder_id not in submitted:
            try:
                body = client.verify(holder_id)
            except CertisError:
                submitted[holder_id] = UNVERIFIED
            else:
                submitted[holder_id] = _read_body(body, holder_id)
        outcomes.append({"account_id": account_id,
                         "outcome": submitted[holder_id]})
    if not outcomes:
        return False, None, E_NOT_FOUND
    return True, outcomes, None
