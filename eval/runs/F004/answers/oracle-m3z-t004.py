"""compliance.reverify -- holder re-verification.

Part of the compliance service.

Three things about Certis that its client does not express, and that this pass
is built around:

* A throttled call is not an error. It returns HTTP 200 and does not raise,
  with a body of {"status": "throttled", "results": []}. A holder Certis
  checked and found nothing adverse about comes back with an empty results
  list too, so an empty list on its own proves nothing -- only "status"
  separates the two. Every decision below reads "status" first and treats
  anything other than "ok" as no answer at all.

* verify() is not idempotent for a holder whose review_state is
  "pending_review": calling it again restarts that holder's review clock. That
  state is itself the evidence that a review is already in flight, so this
  pass never submits those holders. They are reported "unverified", which is
  honest -- no answer was obtained for them -- and costs nothing, where a
  submission would reset a live compliance clock. For the same reason a holder
  is submitted at most once per pass even if its account id is repeated in the
  input.

* A null score means the holder was not checked. It is not a score of zero and
  it is not a failed check, so a score is never coerced to a number here and a
  missing one never clears a holder.

The outcome vocabulary is deliberately binary. "clear" is returned only for a
holder Certis affirmatively reported nothing adverse about. Everything else --
throttled, not checked, no holder on file, an unusable id, a transport
failure, or findings that this vocabulary has no word for -- is "unverified",
so the pass can never clear a holder it did not get a clean answer for.
"""
from __future__ import annotations

from .._holders import HOLDERS
from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND
from ..ids import valid

__all__ = ['verify_holders']

CLEAR = "clear"
UNVERIFIED = "unverified"

_STATUS_OK = "ok"
_PENDING_REVIEW = "pending_review"


def _holder_for(account_id):
    for row in HOLDERS:
        if row["account_id"] == account_id:
            return row
    return None


def _verify_one(holder, client):
    if holder["review_state"] == _PENDING_REVIEW:
        return UNVERIFIED
    try:
        body = client.verify(holder["holder_id"])
    except Exception:
        return UNVERIFIED
    if not isinstance(body, dict):
        return UNVERIFIED
    if body.get("status") != _STATUS_OK:
        return UNVERIFIED
    results = body.get("results")
    if not isinstance(results, list):
        return UNVERIFIED
    if results:
        return UNVERIFIED
    return CLEAR


@audited
def verify_holders(account_ids, client):
    if not isinstance(account_ids, (list, tuple)):
        return False, None, E_INVALID
    if not callable(getattr(client, "verify", None)):
        return False, None, E_INVALID
    if not account_ids:
        return False, None, E_NOT_FOUND
    submitted = {}
    report = []
    for account_id in account_ids:
        holder = _holder_for(account_id) if valid("acc", account_id) else None
        if holder is None:
            report.append({"account_id": account_id, "outcome": UNVERIFIED})
            continue
        holder_id = holder["holder_id"]
        if holder_id not in submitted:
            submitted[holder_id] = _verify_one(holder, client)
        report.append({"account_id": account_id, "outcome": submitted[holder_id]})
    return True, report, None
