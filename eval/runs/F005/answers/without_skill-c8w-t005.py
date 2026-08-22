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
    """The holder on file for `account_id`, or None when there is none."""
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _outcome_for(holder_id, client):
    """Ask Certis about one holder and reduce the body to a single outcome."""
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
    rows = []
    for account_id in account_ids:
        if not valid("acc", account_id):
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        holder_id = _holder_id_for(account_id)
        if holder_id is None:
            rows.append({"account_id": account_id, "holder_id": None,
                         "outcome": UNVERIFIED})
            continue
        rows.append({"account_id": account_id, "holder_id": holder_id,
                     "outcome": _outcome_for(holder_id, client)})
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
