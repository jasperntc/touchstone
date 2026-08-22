"""Certis -- external identity verification.

Submit a holder id, get back a decoded response body.
"""
from __future__ import annotations


class CertisError(Exception):
    """Raised when the transport itself fails."""


class CertisClient:
    """Client for the Certis v3 endpoint.

    A response body looks like:

        {"results": [{"holder_id": "hld_1", "score": 91, "adverse": false}]}

    An empty `results` list means Certis found nothing to report. `adverse`
    marks a finding that needs review.

    `transport` is any callable taking (path, payload) and returning the
    decoded body. The default is wired up by meridian.vendor at import time in
    production; tests pass their own.
    """

    def __init__(self, api_key, transport=None):
        self.api_key = api_key
        self._transport = transport
        self.calls = 0

    def verify(self, holder_id):
        """Submit one holder for re-verification and return the response body."""
        if self._transport is None:
            raise CertisError("no transport configured")
        self.calls += 1
        return self._transport("/v3/verify", {"holder_id": holder_id})
