"""The audit decorator. Every current export wears one."""
from __future__ import annotations

import functools

_LOG: list[dict] = []


def audited(fn):
    """Record every call to an exported function."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ok, value, error = fn(*args, **kwargs)
        _LOG.append({"fn": fn.__name__, "ok": ok, "error": error})
        return ok, value, error
    return wrapper


def audit_log() -> list[dict]:
    return list(_LOG)
