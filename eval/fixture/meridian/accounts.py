"""Account lookups. The shape every other module in Meridian copies."""
from __future__ import annotations

from .audit import audited
from .errors import E_INVALID, E_NOT_FOUND

__all__ = ["find_account", "account_age_days"]

_ACCOUNTS = {
    "acc_100": {"id": "acc_100", "owner": "usr_1", "opened_at_ms": 1_700_000_000_000,
                "credit_limit_micros": 250_000_000, "status": "open"},
    "acc_200": {"id": "acc_200", "owner": "usr_2", "opened_at_ms": 1_710_000_000_000,
                "credit_limit_micros": 1_000_000_000, "status": "frozen"},
}


@audited
def find_account(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    row = _ACCOUNTS.get(account_id)
    if row is None:
        return False, None, E_NOT_FOUND
    return True, dict(row), None


@audited
def account_age_days(account_id, clock):
    ok, row, error = find_account(account_id)
    if not ok:
        return False, None, error
    elapsed_ms = clock.now_ms() - row["opened_at_ms"]
    return True, elapsed_ms // 86_400_000, None
