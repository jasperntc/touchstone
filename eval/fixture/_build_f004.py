#!/usr/bin/env python3
"""Add the F004 surface to the Meridian fixture.

F004 tests information a codebase cannot contain. So the codebase must contain
a plausible integration and NOT the three facts about it, and the obvious
implementation must be confidently wrong rather than merely uncertain -- a
control that sensibly says "I don't know the rate limit, please confirm" would
measure nothing.

WHAT IS DELIBERATELY ABSENT FROM EVERY FILE THIS WRITES

    a1  a throttled call returns HTTP 200 with status "throttled" and an empty
        results list. It is not an error and it does not raise. Treating an
        empty result as "no match" records an unverified holder as clean.
    a2  verify() is not idempotent for a holder already in pending_review:
        calling it again restarts the review clock.
    a3  a null score means NOT CHECKED, not zero.

None of the three is deducible from the client, the store, or any docstring
here. All three are the shape of runbook and incident knowledge.

WHY A NEW INTEGRATION RATHER THAN AN EXISTING ONE

F003 died partly on arguments about whether a minority pattern or the local
majority was authoritative -- controls found the conventions and then reasoned
about which to follow. Nothing in the tree calls Certis yet, so there is no
precedent to copy and no majority to argue with.

PROSE DISCIPLINE

Every docstring below is neutral by construction. The F003 writeup found four
root modules stating conventions outright in the universal-quantifier
declarative form ("Every current entry point validates through here"), which
--audit could not see at the time. It can now, and it runs over this output.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent / "meridian"


def main() -> None:
    (ROOT / "vendor").mkdir(exist_ok=True)
    (ROOT / "vendor" / "__init__.py").write_text(
        '"""Third-party integrations."""\n', encoding="utf-8", newline="\n")
    (ROOT / "compliance").mkdir(exist_ok=True)
    (ROOT / "compliance" / "__init__.py").write_text(
        '"""compliance."""\n', encoding="utf-8", newline="\n")

    # The client. Documents its call shape and its response shape, and says
    # nothing about budgets, idempotency or what a null score means -- those
    # are the three things being withheld. Note that `verify` returns the
    # decoded body whatever it contains: there is no error path to notice.
    (ROOT / "vendor" / "certis.py").write_text('''"""Certis -- external identity verification.

Submit a holder id, get back a decoded response body.
"""
from __future__ import annotations


class CertisError(Exception):
    """Raised when the transport itself fails."""


class CertisClient:
    """Client for the Certis v3 endpoint.

    A response body looks like:

        {"status": "ok", "results": [{"holder_id": "hld_1", "score": 91}]}

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
''', encoding="utf-8", newline="\n")

    # The holder store. 180 accounts: a third in pending_review, leaving 120
    # settled.
    #
    # The count is load-bearing and was wrong at first. With 150 accounts a
    # correct answer skips the 50 pending_review holders and makes exactly 100
    # calls -- precisely the budget -- so the throttle never fires for it and
    # a1 could only ever be observed in an answer that had already failed a2.
    # That is F002's second defect exactly: a check that cannot fail
    # independently of another one. At 180 the correct answer still makes 120
    # calls and still meets the throttle, so a1 and a2 move separately.
    #
    # `review_state` is a plain data field and nothing here says what it means.
    rows = []
    for i in range(180):
        state = "pending_review" if i % 3 == 1 else "settled"
        rows.append(
            '    {{"account_id": "acc_{a}", "holder_id": "hld_{h}", '
            '"review_state": "{s}"}},\n'.format(a=200 + i, h=400 + i, s=state))
    (ROOT / "_holders.py").write_text(
        '"""Account holders.\n\n'
        'Written by the nightly import; do not edit by hand.\n"""\n'
        'from __future__ import annotations\n\n'
        'HOLDERS = [\n' + "".join(rows) + ']\n',
        encoding="utf-8", newline="\n")

    print("vendor/certis.py, compliance/, _holders.py ({} rows)".format(len(rows)))
    print("total fixture files:", sum(1 for _ in ROOT.rglob("*.py")))


if __name__ == "__main__":
    main()
