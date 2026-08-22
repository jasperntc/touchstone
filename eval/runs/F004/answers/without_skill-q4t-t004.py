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


def _holder_id_for(account_id):
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _outcome_for(account_id, client):
    if not valid("acc", account_id):
        return UNVERIFIED
    holder_id = _holder_id_for(account_id)
    if holder_id is None:
        return UNVERIFIED
    try:
        body = client.verify(holder_id)
    except CertisError:
        return UNVERIFIED
    if not isinstance(body, dict) or body.get("status") != "ok":
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    for result in results:
        if isinstance(result, dict) and result.get("holder_id") == holder_id:
            return CLEAR
    return UNVERIFIED


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    rows = [{"account_id": a, "outcome": _outcome_for(a, client)}
            for a in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
