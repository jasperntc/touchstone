"""compliance.reverify -- holder re-verification.

Reference answer for t005. Never shown to an answerer. Knows the three Certis
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
    outcomes = []
    for account_id in account_ids:
        holder = by_account.get(account_id) if isinstance(account_id, str) else None
        if holder is None:
            outcomes.append({"account_id": account_id, "outcome": "unverified"})
            continue
        # Re-submitting a holder already under review restarts their clock.
        if holder["review_state"] == "pending_review":
            outcomes.append({"account_id": account_id, "outcome": "unverified"})
            continue

        body = client.verify(holder["holder_id"])
        # A throttled call carries an undocumented status key and no results.
        if not isinstance(body, dict) or body.get("status", "ok") != "ok":
            outcomes.append({"account_id": account_id, "outcome": "unverified"})
            continue
        rows = body.get("results") or []
        if any(r.get("score") is None for r in rows):
            # Null score means not checked, whatever `adverse` says beside it.
            outcomes.append({"account_id": account_id, "outcome": "unverified"})
            continue
        if any(r.get("adverse") for r in rows):
            outcomes.append({"account_id": account_id, "outcome": "flagged"})
            continue
        outcomes.append({"account_id": account_id, "outcome": "clear"})

    return True, outcomes, None
