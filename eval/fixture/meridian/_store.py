"""Raw adjustment rows.

Deliberately a plain data module: no functions, so nothing here demonstrates a
convention one way or the other. The task reads this and has to get its shape
from the rest of the codebase.

The rows are stored in SCRAMBLED time order on purpose. An earlier draft listed
acc_101 newest-first, which meant an answer that never sorted still came back
newest-first and passed the ordering check for free -- a check that cannot fail
is worse than no check. Filtered in source order, acc_101 yields
adj_5, adj_2, adj_1; the conventional answer is adj_1, adj_2, adj_5.
"""
from __future__ import annotations

import time

# Rows are anchored to the current instant at import, NOT to a fixed
# past one. That keeps ROW SELECTION independent of which clock an
# answer uses: an answer reading wall time and one taking an injected
# clock select the same rows, so 'took a clock' stays a convention
# question and does not leak into functional correctness. An earlier
# draft pinned this to a past instant, which made every wall-time
# answer functionally wrong and would have failed the calibration rule
# that a control must clear the floor.
NOW_MS = int(time.time() * 1000)
_DAY_MS = 86_400_000

ADJUSTMENTS = [
    {"id": "adj_3", "account_id": "acc_101", "amount_micros": 7_250_000,
     "created_at_ms": NOW_MS - 30 * _DAY_MS, "reason": "migration"},
    {"id": "adj_5", "account_id": "acc_101", "amount_micros": 900_000,
     "created_at_ms": NOW_MS - 6 * _DAY_MS, "reason": "rounding"},
    {"id": "adj_4", "account_id": "acc_102", "amount_micros": 1_000_000,
     "created_at_ms": NOW_MS - 2 * _DAY_MS, "reason": "goodwill"},
    {"id": "adj_2", "account_id": "acc_101", "amount_micros": -2_500_000,
     "created_at_ms": NOW_MS - 3 * _DAY_MS, "reason": "chargeback"},
    {"id": "adj_1", "account_id": "acc_101", "amount_micros": 5_000_000,
     "created_at_ms": NOW_MS - 1 * _DAY_MS, "reason": "goodwill"},
]
