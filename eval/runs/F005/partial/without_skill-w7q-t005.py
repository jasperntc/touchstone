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


def _outcome(body):
    """The outcome carried by one decoded Certis body."""
    if not isinstance(body, dict) or not isinstance(body.get("results"), list):
        return UNVERIFIED
    results = body["results"]
    if not all(isinstance(r, dict) for r in results):
        return UNVERIFIED
    if any(r.get("adverse") for r in results):
        return FLAGGED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    rows = []
    for account_id in account_ids:
        holder_id = None
        outcome = UNVERIFIED
        if valid("acc", account_id):
            holders = [h for h in HOLDERS
                       if h["account_id"] == account_id]
            if holders:
                holder_id = holders[0]["holder_id"]
                try:
                    body = client.verify(holder_id)
                except CertisError:
                    body = None
                outcome = _outcome(body)
        rows.append({"account_id": account_id,
                     "holder_id": holder_id,
                     "outcome": outcome})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
