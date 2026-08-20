"""The only source of time in current Meridian code."""
from __future__ import annotations


class Clock:
    def now_ms(self) -> int:
        raise NotImplementedError


class FixedClock(Clock):
    def __init__(self, now_ms: int) -> None:
        self._now_ms = now_ms

    def now_ms(self) -> int:
        return self._now_ms
