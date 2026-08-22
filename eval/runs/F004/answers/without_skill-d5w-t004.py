"""compliance.reverify -- reverify.

Part of the compliance service.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders']

_CLEAR = "clear"
_UNVERIFIED = "unverified"


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list) or not account_ids:
        return False, None, E_INVALID
    outcomes = [{"account_id": account_id,
                 "outcome": _outcome_for(account_id, client)}
                for account_id in account_ids]
    return True, outcomes, None


def _outcome_for(account_id, client):
    if not valid("acc", account_id):
        return _UNVERIFIED
    rows = [r for r in HOLDERS
            if r["account_id"] == account_id]
    if not rows:
        return _UNVERIFIED
    holder_id = rows[0]["holder_id"]
    try:
        body = client.verify(holder_id)
    except CertisError:
        return _UNVERIFIED
    if not isinstance(body, dict) or body.get("status") != "ok":
        return _UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return _UNVERIFIED
    findings = [f for f in results
                if isinstance(f, dict) and f.get("holder_id") == holder_id]
    if findings:
        return _UNVERIFIED
    return _CLEAR
