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

ALL_OUTCOMES = (CLEAR, FLAGGED, UNVERIFIED)


def _holder_id(account_id):
    """The holder id on file for an account, or None when there is none."""
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _outcome(holder_id, client):
    """CLEAR, FLAGGED or UNVERIFIED for one holder Certis was asked about."""
    try:
        body = client.verify(holder_id)
    except CertisError:
        return UNVERIFIED
    if not isinstance(body, dict):
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    for result in results:
        if not isinstance(result, dict):
            return UNVERIFIED
        if result.get("adverse"):
            return FLAGGED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not account_ids:
        return False, None, E_NOT_FOUND
    report = []
    for account_id in account_ids:
        holder_id = _holder_id(account_id) if valid("acc", account_id) else None
        if holder_id is None:
            outcome = UNVERIFIED
        else:
            outcome = _outcome(holder_id, client)
        report.append({"account_id": account_id,
                       "holder_id": holder_id,
                       "outcome": outcome})
    return True, report, None
