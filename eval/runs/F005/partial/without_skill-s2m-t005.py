"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders', 'CLEAR', 'FLAGGED', 'UNVERIFIED', 'ALL_OUTCOMES']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"

ALL_OUTCOMES = (CLEAR, FLAGGED, UNVERIFIED)


def _holder_id(account_id):
    """The holder on file for one account, or None."""
    for h in HOLDERS:
        if h["account_id"] == account_id:
            return h["holder_id"]
    return None


def _outcome(body):
    """Map one Certis response body onto an outcome."""
    if not isinstance(body, dict):
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    for r in results:
        if not isinstance(r, dict):
            return UNVERIFIED
        if r.get("adverse"):
            return FLAGGED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    """Re-verify the holder behind each account id through Certis."""
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    rows = []
    for account_id in account_ids:
        holder_id = _holder_id(account_id) if valid("acc", account_id) else None
        if holder_id is None:
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        try:
            outcome = _outcome(client.verify(holder_id))
        except CertisError:
            outcome = UNVERIFIED
        rows.append({"account_id": account_id, "holder_id": holder_id,
                     "outcome": outcome})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
