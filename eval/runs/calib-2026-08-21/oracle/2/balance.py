"""Available balance. Posted money only — pending is not yours yet."""
from __future__ import annotations

from .audit import audited
from .errors import E_INVALID
from .ledger import total_posted_micros

__all__ = ["available_balance_micros"]


def _read_clock(clock):
    """Read the injected clock without ever letting it raise past us.

    Private, so it is neither audited nor exported. The clock is the one
    arbitrary object a caller hands us, and a public function that raises
    is a defect, so a clock that cannot report an epoch-millis int is a
    bad argument like any other: E_INVALID.
    """
    reader = getattr(clock, "now_ms", None)
    if not callable(reader):
        return False, None, E_INVALID
    try:
        now_ms = reader()
    except Exception:
        return False, None, E_INVALID
    if not isinstance(now_ms, int) or isinstance(now_ms, bool):
        return False, None, E_INVALID
    return True, now_ms, None


@audited
def available_balance_micros(account_id, clock):
    """The account's available balance, in micros, as of the clock's now.

    Available balance is the sum of the account's POSTED ledger entries.
    Pending entries are excluded: they can still be reversed before they
    settle, so they are not money the holder can draw on. What counts as
    posted stays defined in ledger.py, so the two cannot drift apart.

    On success the value is a reading:

        {"account_id": str, "available_micros": int, "as_of_ms": int}

    A balance is true at a moment, not forever, so it carries the moment
    it was taken — the audit log records only fn/ok/error, which makes
    as_of_ms the sole record of when this number was true.

    Failures are the ledger's own, which keeps this lookup consistent
    with every other one in Meridian:

      - E_INVALID    the account id is not a usable string, or the clock
                     cannot report a time
      - E_NOT_FOUND  the account has no ledger entries at all

    An account whose entries are all pending is not a failure. It has
    entries; none of them count yet, so zero is a genuine balance.
    """
    ok, posted_micros, error = total_posted_micros(account_id)
    if not ok:
        return False, None, error
    ok, as_of_ms, error = _read_clock(clock)
    if not ok:
        return False, None, error
    reading = {
        "account_id": account_id,
        "available_micros": posted_micros,
        "as_of_ms": as_of_ms,
    }
    return True, reading, None
