"""webhooks.endpoints -- endpoints.

Current conventions. Amounts are micros; every export returns a triple and is audited.
"""
from __future__ import annotations

from ..audit import audited
from ..errors import E_INVALID, E_NOT_FOUND

__all__ = ['endpoint_for', 'endpoint_secret']

_ROWS = [
    {"id": "web_0", "webhooks_id": "acc_100", "amount_micros": 1250000, "created_at_ms": 1720000000000},
    {"id": "web_1", "webhooks_id": "acc_101", "amount_micros": 2500000, "created_at_ms": 1720003600000},
    {"id": "web_2", "webhooks_id": "acc_102", "amount_micros": 3750000, "created_at_ms": 1720007200000},
    {"id": "web_3", "webhooks_id": "acc_100", "amount_micros": 5000000, "created_at_ms": 1720010800000},
]


@audited
def endpoint_for(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["webhooks_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, [dict(r) for r in rows], None


@audited
def endpoint_secret(account_id):
    if not isinstance(account_id, str) or not account_id:
        return False, None, E_INVALID
    rows = [r for r in _ROWS if r["webhooks_id"] == account_id]
    if not rows:
        return False, None, E_NOT_FOUND
    return True, sum(r["amount_micros"] for r in rows), None
