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


def _holder_id_for(account_id):
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _certis_outcome(client, holder_id):
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
        if isinstance(result, dict) and result.get("adverse"):
            return FLAGGED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    outcomes = []
    for account_id in account_ids:
        holder_id = _holder_id_for(account_id) if valid("acc", account_id) else None
        if holder_id is None:
            outcomes.append({"account_id": account_id,
                             "holder_id": None,
                             "outcome": UNVERIFIED})
            continue
        outcomes.append({"account_id": account_id,
                         "holder_id": holder_id,
                         "outcome": _certis_outcome(client, holder_id)})
    if not outcomes:
        return False, None, E_NOT_FOUND
    return True, outcomes, None
