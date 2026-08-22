"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid

__all__ = ['verify_holders']

CLEAR = "clear"
UNVERIFIED = "unverified"


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    rows = [{"account_id": account_id,
             "outcome": _outcome_for(account_id, client)}
            for account_id in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None


def _outcome_for(account_id, client):
    if not valid("acc", account_id):
        return UNVERIFIED
    holders = [r for r in HOLDERS
               if r["account_id"] == account_id]
    if not holders:
        return UNVERIFIED
    holder_id = holders[0]["holder_id"]
    try:
        body = client.verify(holder_id)
    except Exception:
        return UNVERIFIED
    if not isinstance(body, dict) or body.get("status") != "ok":
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    for finding in results:
        if not isinstance(finding, dict):
            return UNVERIFIED
        if finding.get("holder_id") == holder_id:
            return UNVERIFIED
    return CLEAR
