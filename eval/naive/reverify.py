"""compliance.reverify -- holder re-verification.

Calibration draft: the obvious implementation. Look up the holder, submit it,
read the response, report what came back. It is competent, it follows the house
conventions it can see, and it is wrong in all three of the ways the absent
facts describe -- which is the point. If it ever passes an `absent` check, that
check is not measuring absent information.
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
    outcomes = {}
    for account_id in account_ids:
        holder = by_account.get(account_id) if isinstance(account_id, str) else None
        if holder is None:
            outcomes[account_id] = "unverified"
            continue
        body = client.verify(holder["holder_id"])
        rows = body.get("results")
        outcomes[account_id] = "clear" if rows is not None else "unverified"
    return True, outcomes, None
