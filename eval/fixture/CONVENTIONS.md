# Meridian house conventions

Eight rules. They are this codebase's own choices, not industry standards.
Delivered only in the `oracle` condition.

Each is phrased to match what the current code actually does. Rule 6 in the
F001 fixture read as an imperative ("take a clock argument") and one oracle
answer bolted a clock onto a function that needed no time at all, scoring worse
than the control. A rule that overstates itself makes the upper control worse,
which is the opposite of its job.

1. **Money is micros.** Millionths of a currency unit, as `int`, on a field or
   variable whose name ends `_micros`. Never cents, never floats.

2. **Public functions return a triple**, `(ok: bool, value, error: str | None)`.
   Success is `(True, value, None)`; failure is `(False, None, CODE)`.

3. **Failures are codes, never prose.** Every error is a constant from
   `meridian/errors.py`.

4. **Public functions never raise.** Unusable input returns `E_INVALID`.

5. **Every public function is `@audited` and named in `__all__`.**

6. **Functions that need the current time take a `clock` parameter and call
   `clock.now_ms()`.** Never `datetime.now()` or `time.time()`. Functions that
   need no current time take no clock. Timestamps are epoch milliseconds on a
   `*_ms` field.

7. **Identifiers are validated for shape, not just truthiness.** `ids.valid`
   checks the prefix (`acc`, `led`, `pay`, `inv`, `ntf`, `fx`) and the body. A
   wrong-prefix or malformed id is `E_INVALID`, not an account that happens to
   have no rows.

8. **Functions returning a list of rows return them newest first**, ordered by
   the row's `*_at_ms` field descending.
