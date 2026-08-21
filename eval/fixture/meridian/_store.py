"""Adjustment rows.

Written by the nightly import; do not edit by hand.
"""
from __future__ import annotations

import time

_NOW_MS = int(time.time() * 1000)
_DAY_MS = 86_400_000

ADJUSTMENTS = [
    {"id": "adj_15", "account_id": "acc_101", "amount_micros": 900_000,
     "created_at_ms": _NOW_MS - 5 * _DAY_MS, "reason": "rounding"},
    {"id": "adj_31", "account_id": "acc_103", "amount_micros": 1_500_000,
     "created_at_ms": _NOW_MS - 1 * _DAY_MS, "reason": "goodwill"},
    {"id": "adj_23", "account_id": "acc_102", "amount_micros": 3_000_000,
     "created_at_ms": _NOW_MS - 6 * _DAY_MS, "reason": "migration"},
    {"id": "adj_12", "account_id": "acc_101", "amount_micros": 4_000_000,
     "created_at_ms": _NOW_MS - 2 * _DAY_MS, "reason": "goodwill"},
    {"id": "adj_41", "account_id": "acc_104", "amount_micros": 800_000,
     "created_at_ms": _NOW_MS - 40 * _DAY_MS, "reason": "migration"},
    {"id": "adj_33", "account_id": "acc_103", "amount_micros": 2_200_000,
     "created_at_ms": _NOW_MS - 4 * _DAY_MS, "reason": "rounding"},
    {"id": "adj_17", "account_id": "acc_101", "amount_micros": 7_250_000,
     "created_at_ms": _NOW_MS - 30 * _DAY_MS, "reason": "migration"},
    {"id": "adj_21", "account_id": "acc_102", "amount_micros": 1_000_000,
     "created_at_ms": _NOW_MS - 1 * _DAY_MS, "reason": "goodwill"},
    {"id": "adj_14", "account_id": "acc_101", "amount_micros": 3_000_000,
     "created_at_ms": _NOW_MS - 4 * _DAY_MS, "reason": "correction"},
    {"id": "adj_32", "account_id": "acc_103", "amount_micros": 0,
     "created_at_ms": _NOW_MS - 2 * _DAY_MS, "reason": "no-op"},
    {"id": "adj_11", "account_id": "acc_101", "amount_micros": 5_000_000,
     "created_at_ms": _NOW_MS - 1 * _DAY_MS, "reason": "goodwill"},
    {"id": "adj_24", "account_id": "acc_102", "amount_micros": 500_000,
     "created_at_ms": _NOW_MS - 20 * _DAY_MS, "reason": "migration"},
    {"id": "adj_16", "account_id": "acc_101", "amount_micros": 1_100_000,
     "created_at_ms": _NOW_MS - 6 * _DAY_MS, "reason": "rounding"},
    {"id": "adj_22", "account_id": "acc_102", "amount_micros": 2_000_000,
     "created_at_ms": _NOW_MS - 3 * _DAY_MS, "reason": "chargeback"},
    {"id": "adj_13", "account_id": "acc_101", "amount_micros": -2_500_000,
     "created_at_ms": _NOW_MS - 3 * _DAY_MS, "reason": "chargeback"},
]
