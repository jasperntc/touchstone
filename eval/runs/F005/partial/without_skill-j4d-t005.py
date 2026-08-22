"""compliance.reverify -- reverify.

Part of the compliance service.

Every account handed in gets exactly one outcome: CLEAR when Certis answered
and reported nothing adverse, FLAGGED when Certis answered and reported
something adverse, UNVERIFIED when no usable answer was obtained -- an
unusable id, no holder on file, a transport failure, or a body Certis did
not fill in as documented.
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

ALL_OUTCOMES = (CLEAR, FLAGGED, UNVERIFIED)


def _outcome_for(account_id, client):
    if not valid("acc", account_id):
        return UNVERIFIED
    holders = [h for h in HOLDERS
               if h["account_id"] == account_id]
    if not holders:
        return UNVERIFIED
    try:
        body = client.verify(holders[0]["holder_id"])
    except CertisError:
        return UNVERIFIED
    if not isinstance(body, dict):
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    if not all(isinstance(r, dict) for r in results):
        return UNVERIFIED
    if any(r.get("adverse") for r in results):
        return FLAGGED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, list):
        return False, None, E_INVALID
    rows = [{"account_id": a, "outcome": _outcome_for(a, client)}
            for a in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
