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


def _holder_id(account_id):
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _certis_status(client, holder_id):
    try:
        body = client.verify(holder_id)
    except CertisError:
        return "unverified"
    if not isinstance(body, dict):
        return "unverified"
    results = body.get("results")
    if not isinstance(results, list):
        return "unverified"
    for result in results:
        if isinstance(result, dict) and result.get("adverse"):
            return "flagged"
    return "clear"


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    outcomes = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            status = "unverified"
        else:
            holder_id = _holder_id(account_id)
            if holder_id is None:
                status = "unverified"
            else:
                status = _certis_status(client, holder_id)
        outcomes.append({"account_id": account_id, "status": status})
    if not outcomes:
        return False, None, E_NOT_FOUND
    return True, outcomes, None
