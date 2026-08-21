"""compliance.reverify -- holder re-verification.

Reference answer for t004. Never shown to an answerer. Knows the three Certis
facts, so --self-test can prove every check is satisfiable.
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
        # Re-submitting a holder already under review restarts their clock.
        if holder["review_state"] == "pending_review":
            outcomes[account_id] = "unverified"
            continue

        body = client.verify(holder["holder_id"])
        # A throttled call is a 200 with an empty results list, not an error.
        if body.get("status") != "ok":
            outcomes[account_id] = "unverified"
            continue
        rows = body.get("results") or []
        # An empty list on a status=ok response means Certis
        # found nothing adverse. A null score means not checked.
        if rows and rows[0].get("score") is None:
            outcomes[account_id] = "unverified"
            continue
        outcomes[account_id] = "clear"

    return True, outcomes, None
