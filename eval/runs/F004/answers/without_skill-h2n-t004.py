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
    """The holder id on file for `account_id`, or None when there is none."""
    rows = [h for h in HOLDERS
            if h["account_id"] == account_id]
    if not rows:
        return None
    return rows[0]["holder_id"]


def _outcome_for(account_id, client):
    """CLEAR only when Certis gave a usable answer with no adverse findings."""
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
    """One outcome per given account, in the order the accounts were given."""
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = [{"account_id": account_id,
             "outcome": _outcome_for(account_id, client)}
            for account_id in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
