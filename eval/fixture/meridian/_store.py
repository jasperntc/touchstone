"""Adjustment rows.

Written by the nightly import; do not edit by hand.
"""
from __future__ import annotations

import time

_NOW_MS = int(time.time() * 1000)
_DAY_MS = 86_400_000

ADJUSTMENTS = [
    {"id": "adj_3", "account_id": "acc_101", "amount_micros": 7_250_000,
     "created_at_ms": _NOW_MS - 30 * _DAY_MS, "reason": "migration"},
    {"id": "adj_5", "account_id": "acc_101", "amount_micros": 900_000,
     "created_at_ms": _NOW_MS - 6 * _DAY_MS, "reason": "rounding"},
    {"id": "adj_4", "account_id": "acc_102", "amount_micros": 1_000_000,
     "created_at_ms": _NOW_MS - 2 * _DAY_MS, "reason": "goodwill"},
    {"id": "adj_2", "account_id": "acc_101", "amount_micros": -2_500_000,
     "created_at_ms": _NOW_MS - 3 * _DAY_MS, "reason": "chargeback"},
    {"id": "adj_1", "account_id": "acc_101", "amount_micros": 5_000_000,
     "created_at_ms": _NOW_MS - 1 * _DAY_MS, "reason": "goodwill"},
]
