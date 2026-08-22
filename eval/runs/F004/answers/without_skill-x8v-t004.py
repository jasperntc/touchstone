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


def _outcome(account_id, client):
    """One account's outcome. Anything short of a usable answer is UNVERIFIED."""
    if not valid("acc", account_id):
        return UNVERIFIED
    rows = [h for h in HOLDERS if h["account_id"] == account_id]
    if not rows:
        return UNVERIFIED
    holder_id = rows[0]["holder_id"]
    try:
        body = client.verify(holder_id)
    except CertisError:
        return UNVERIFIED
    if not isinstance(body, dict) or body.get("status") != "ok":
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    # An "ok" body carrying a result for the holder we asked about is Certis
    # saying it has nothing adverse on file; anything else answered nothing.
    for result in results:
        if isinstance(result, dict) and result.get("holder_id") == holder_id:
            return CLEAR
    return UNVERIFIED


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    if not account_ids:
        return False, None, E_NOT_FOUND
    rows = [{"account_id": a, "outcome": _outcome(a, client)}
            for a in account_ids]
    return True, rows, None
