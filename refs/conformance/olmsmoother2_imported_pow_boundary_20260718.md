# OLMSmoother2 imported pow boundary audit - 2026-07-18

Verdict: `PASS_IMPORTED_POW_BOUNDARY_CLASSIFIED_NOT_UCRT_ONLY`

## Binary Fact

The checked AEX imports `api-ms-win-crt-math-l1-1-0.dll!pow`. The call at `0x180002d23` uses double arguments in `XMM0/XMM1`; `0x180002d28` then executes `CVTSD2SS`.

## Numerical Classification

- Guest input: `0x3fdfa568c0e8f2a7`; exponent: `0x4003333333333333`.
- Darwin/Python pow then float conversion: `0x3e3ce703`.
- Retained Windows polygon word: `0x3e3ce706`.
- Difference: `3` float32 ULP.
- A 110-digit Decimal `exp(y*ln(x))` oracle agrees with the Darwin result at the float32 rounding boundary.
- Therefore the retained word cannot presently be classified as a UCRT-only difference for the same input. The Windows pow input and return must be captured in one run.

## PF8 Sensitivity

The bounded natural AEX path replaced exactly `3` RGB pow returns with the retained word. Class bytes, descriptor, polygon weights, and final cce0 float words remained bitwise equal. The polygon RGB difference itself remained visible, proving the test was not inert.

For this bounded case_0012 witness, the retained three-ULP RGB difference does not reach cce0 output and therefore cannot change its PF8 writer result.

## Binary-grounded Strategy

- Capture XMM0/XMM1 at 0x180002d23 and XMM0 before 0x180002d28 on Windows for the accepted pixel.
- If the input bits match, store a keyed UCRT return oracle and investigate the unexpected error before production use.
- If the input bits differ, fix the PF8 host adapter/conversion provenance rather than compensating in pow.
- For PF8 production, generate a 256-code (or premultiplied code-pair) Windows-grounded sRGB decode table and verify full AE cases.
- For PF16/PF32, use captured UCRT boundary vectors plus a deterministic implementation; do not reuse a PF8 LUT as a broad fix.

## Reproduction

```sh
python3 tools/emulation/audit_olmsmoother2_imported_pow_boundary_20260718.py
python3 tools/emulation/test_olmsmoother2_imported_pow_boundary_20260718.py
```
