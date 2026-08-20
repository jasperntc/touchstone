"""Identifier shapes. Every current entry point validates through here."""
from __future__ import annotations

PREFIXES = ("acc", "led", "pay", "inv", "ntf", "fx")


def valid(prefix: str, value) -> bool:
    """True when `value` is a well-formed id with the given prefix."""
    if prefix not in PREFIXES:
        return False
    if not isinstance(value, str) or not value:
        return False
    head, _, rest = value.partition("_")
    return head == prefix and rest.isalnum() and len(rest) > 0
