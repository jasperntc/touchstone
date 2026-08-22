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

_PENDING_REVIEW = "pending_review"


def _holder_for(account_id):
    """The holder row for one account, or None."""
    return next((h for h in HOLDERS if h["account_id"] == account_id), None)


def _read_body(body, holder_id):
    """Read one Certis response body. Returns (outcome, ask_again).

    `ask_again` is True only when Certis declined to look at all, so asking
    again could still produce an answer.
    """
    if not isinstance(body, dict):
        return UNVERIFIED, False
    if body.get("status") == "throttled":
        # A throttled call is HTTP 200 with an empty `results` and does not
        # raise. Certis never looked, so this is not "nothing to report".
        return UNVERIFIED, True
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED, False
    if not results:
        # Documented on CertisClient: an empty `results` means Certis looked
        # and found nothing to report.
        return CLEAR, False
    entry = next((e for e in results
                  if isinstance(e, dict) and e.get("holder_id") == holder_id), None)
    if entry is None:
        # Certis answered, but not about this holder.
        return UNVERIFIED, False
    if entry.get("score") is None:
        # A null score means the holder was not checked. It is not a score of
        # zero, and the `adverse` sitting beside it is not a no-adverse
        # finding.
        return UNVERIFIED, False
    adverse = entry.get("adverse")
    if adverse is None:
        return UNVERIFIED, False
    return (FLAGGED if adverse else CLEAR), False


def _verify_one(account_id, client, attempts):
    """One account in, one outcome row out. Never raises for one bad account."""
    row = {"account_id": account_id, "holder_id": None, "outcome": UNVERIFIED}
    if not valid("acc", account_id):
        return row
    holder = _holder_for(account_id)
    if holder is None:
        return row
    holder_id = holder.get("holder_id")
    row["holder_id"] = holder_id
    # verify() is not idempotent for a holder under review: calling it again
    # restarts that holder's review clock. Those holders get one call, never a
    # second one, whatever the retry budget says.
    budget = 1 if holder.get("review_state") == _PENDING_REVIEW else attempts
    for _ in range(budget):
        try:
            body = client.verify(holder_id)
        except CertisError:
            continue
        outcome, ask_again = _read_body(body, holder_id)
        if not ask_again:
            row["outcome"] = outcome
            return row
    return row


@audited
def verify_holders(account_ids, client, attempts=1):
    """Re-verify the holder behind each account id through Certis.

    Reports one row per id given, in the order given:
    `{"account_id": ..., "holder_id": ..., "outcome": ...}`, where outcome is
    exactly one of `clear`, `flagged`, or `unverified`. Nothing is dropped: an
    unusable id, an account with no holder, a transport failure, a throttled
    call, and a holder Certis did not actually check all report `unverified`
    rather than disappearing or passing as `clear`.

    `attempts` is the ceiling on how many times one holder is asked about
    after Certis declines to look. It defaults to one call per holder, and a
    holder whose review is pending is held to one call regardless, because a
    second verify() restarts that holder's review clock.
    """
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        return False, None, E_INVALID
    rows = [_verify_one(account_id, client, attempts) for account_id in account_ids]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, rows, None
