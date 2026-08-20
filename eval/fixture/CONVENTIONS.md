# Meridian house conventions

Six rules. They are not industry standards and no model can know them from
training — they are this codebase's arbitrary choices, which is the whole point
of using them to calibrate.

Every one of them is visible in the committed code. None of them is written
down anywhere the answerer can read during a run: this file is delivered only
in the `oracle` condition, which exists to prove the instrument has range.

1. **Money is micros.** Millionths of a currency unit, stored as `int`, on a
   field or variable whose name ends `_micros`. Never cents, never floats.

2. **Public functions return a triple**, `(ok: bool, value, error: str | None)`.
   On success `(True, value, None)`; on failure `(False, None, CODE)`.

3. **Failures are codes, never prose.** Every error is one of the constants in
   `meridian/errors.py`. A free-text error message is a defect.

4. **Public functions never raise.** A bad argument returns `E_INVALID`; it
   does not raise `ValueError`.

5. **Every public function is `@audited` and listed in `__all__`.** A public
   function missing either is invisible to compliance and is rejected on sight.

6. **Time is injected.** Take a `clock` argument and call `clock.now_ms()`.
   `datetime.now()` and `time.time()` appear nowhere in this codebase.
   Timestamps are epoch milliseconds on a field named `*_ms`.
