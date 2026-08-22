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

_CLEAR = "clear"
_FLAGGED = "flagged"
_UNVERIFIED = "unverified"


def _holder_id_for(account_id):
    """The holder id on record for `account_id`, or None when there is none."""
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _outcome_for(client, holder_id):
    """Submit one holder to Certis and reduce the reply to a single outcome."""
    try:
        body = client.verify(holder_id)
    except CertisError:
        return _UNVERIFIED
    if not isinstance(body, dict):
        return _UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return _UNVERIFIED
    for result in results:
        if isinstance(result, dict) and result.get("adverse"):
            return _FLAGGED
    return _CLEAR


@audited
def verify_holders(account_ids, client):
    """Re-verify each account's holder through Certis, one outcome per account."""
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            rows.append({"account_id": account_id, "outcome": _UNVERIFIED})
            continue
        holder_id = _holder_id_for(account_id)
        if holder_id is None:
            rows.append({"account_id": account_id, "outcome": _UNVERIFIED})
            continue
        rows.append({"account_id": account_id,
                     "outcome": _outcome_for(client, holder_id)})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
