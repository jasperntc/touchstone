"""The only source of time in Meridian.

Nothing in this codebase calls datetime.now() or time.time(). A clock is
passed in, so every test can pin it and every audit entry is reproducible.
"""
from __future__ import annotations


class Clock:
    def now_ms(self) -> int:
        raise NotImplementedError


class FixedClock(Clock):
    def __init__(self, now_ms: int) -> None:
        self._now_ms = now_ms

    def now_ms(self) -> int:
        return self._now_ms
