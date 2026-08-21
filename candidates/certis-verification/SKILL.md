---
name: certis-verification
description: Rules for submitting account holders to the Certis identity provider. Use when writing or reviewing code that calls CertisClient.verify, re-verifies holders, or interprets a Certis response body. Covers the three ways a Certis response lies about what happened.
---

# Certis verification

Certis answers with HTTP 200 far more often than it has actually verified
anybody. All three rules below exist because the failure looks like a success.

## Before you submit: skip holders already under review

`verify()` is **not idempotent for a holder whose `review_state` is
`pending_review`.** Each call restarts their review clock, so a re-verification
pass that submits them silently resets every review in flight.

Filter them out before the call. Do not submit and discard the answer — the
damage is done at submission.

## On the way back: check `status` before `results`

A throttled call returns:

```json
{"status": "throttled", "results": []}
```

**HTTP 200. No exception. Empty list.** Byte-for-byte the same shape as a
holder Certis checked and found nothing adverse about — which is a genuine and
common response. The two are distinguishable *only* by `status`.

Code that reads `results` first records throttled holders as clean. That is the
compliance failure this rule exists to prevent.

```python
body = client.verify(holder_id)
if body.get("status") != "ok":
    return "unverified"          # throttled, degraded, anything not ok
rows = body.get("results") or []
```

An empty `results` on a `status: ok` response **is** a clean result. Do not
treat every empty list as suspicious — that is the opposite error and it
flags people who passed.

## In the row: a null score is not a zero

```json
{"results": [{"holder_id": "hld_400", "score": null}]}
```

`null` means **not checked**. It is not a score of zero and not a failed check.
A holder whose score is null has been through no check at all, so reporting
them clear asserts something nobody established, and reporting them as failed
accuses someone of failing a check they never sat.

```python
if rows and rows[0].get("score") is None:
    return "unverified"
```

## The whole thing

1. Skip `pending_review` holders. Do not submit them.
2. `status != "ok"` → unverified.
3. `score is None` → unverified.
4. Otherwise clear, including when `results` is empty.

## Why this is a skill and not a comment in the client

None of it is visible from the client, the response shape, or any type
signature. It is what a Certis integration teaches you after it has gone wrong
once.
