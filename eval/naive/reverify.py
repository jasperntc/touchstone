"""compliance.reverify -- holder re-verification.

Calibration draft: the obvious implementation, reading only what the client
documents. It follows the house conventions it can see and is wrong in all
three of the ways the absent facts describe. If it ever passes an `absent`
check, that check is not measuring absent information.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ["verify_holders"]


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not account_ids:
        return False, None, E_NOT_FOUND

    by_account = {h["account_id"]: h for h in HOLDERS}
    outcomes = []
    for account_id in account_ids:
        holder = by_account.get(account_id) if isinstance(account_id, str) else None
        if holder is None:
            outcomes.append({"account_id": account_id, "outcome": "unverified"})
            continue
        body = client.verify(holder["holder_id"])
        rows = body.get("results") or []
        outcome = "flagged" if any(r.get("adverse") for r in rows) else "clear"
        outcomes.append({"account_id": account_id, "outcome": outcome})
    return True, outcomes, None
