"""The audit decorator. Every exported function wears one."""
from __future__ import annotations

import functools

_LOG: list[dict] = []


def audited(fn):
    """Record every call to an exported function.

    Compliance reads _LOG. A public function that is not audited is invisible
    to them, which is why the reviewers reject one on sight.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        ok, value, error = fn(*args, **kwargs)
        _LOG.append({"fn": fn.__name__, "ok": ok, "error": error})
        return ok, value, error
    return wrapper


def audit_log() -> list[dict]:
    return list(_LOG)
