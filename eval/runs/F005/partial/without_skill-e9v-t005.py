"""compliance.reverify -- reverify.

Part of the compliance service.

Every account handed in comes back carrying exactly one outcome:

    clear       Certis answered and reported nothing adverse
    flagged     Certis answered and reported something adverse
    unverified  no usable answer was obtained -- an unusable id, no holder
                on file, a transport failure, or a body we cannot read
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID
from ..ids import valid
from ..vendor.certis import CertisError

__all__ = ['verify_holders']

CLEAR = "clear"
FLAGGED = "flagged"
UNVERIFIED = "unverified"

ALL_OUTCOMES = (CLEAR, FLAGGED, UNVERIFIED)


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    outcomes = [{"account_id": account_id,
                 "outcome": _outcome_for(account_id, client)}
                for account_id in account_ids]
    return True, outcomes, None


def _outcome_for(account_id, client):
    if not valid("acc", account_id):
        return UNVERIFIED
    holder_id = _holder_id(account_id)
    if holder_id is None:
        return UNVERIFIED
    try:
        body = client.verify(holder_id)
    except CertisError:
        return UNVERIFIED
    return _read_body(body)


def _holder_id(account_id):
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row["holder_id"]
    return None


def _read_body(body):
    if not isinstance(body, dict):
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    outcome = CLEAR
    for entry in results:
        if not isinstance(entry, dict) or not isinstance(entry.get("adverse"), bool):
            return UNVERIFIED
        if entry["adverse"]:
            outcome = FLAGGED
    return outcome
