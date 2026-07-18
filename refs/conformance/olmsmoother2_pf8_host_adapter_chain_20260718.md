# OLMSmoother2 PF8 host-adapter chain - 2026-07-18

## Decision

The first causal mismatch for current-AEX legacy case `0012` is closed under
the diagnostic PF8 host adapter. This is a binary-grounded intermediate result,
not AE exactness.

## FACT

- Raw PNG `(92,840)` is `[174,174,174,174]`.
- The Windows before-effects pixel is `[119,119,119,174]`.
- PF8 nearest-integer premultiplication `(rgb * alpha + 127) // 255` maps
  `174,174` to `119`.
- Loading `119/255` and applying the grounded sRGB decode produces Mac CLI
  `0.18447499`; the Windows actual-AEX witness is `0.18447503`.
- With the diagnostic adapter, the Mac chain matches the accepted Windows
  class bytes, descriptor `(92,841,1,92,842,2)`, `e170 c=7`, first source
  pixel, and first weight `0.28448275`.
- The complete candidate is still not exact: against the Windows PNG it has
  `max_diff=126`, `nonzero_pixels=15957`, and witness output
  `[224,224,224,239]` versus `[233,233,233,237]`.

## Boundary

The remaining live boundary starts after the first append. The complete
Windows post-`f130` polygon state and live `cce0` input are not captured. Do
not tune the writer, gamma curve, or polygon weights from the PNG residual.

## Reproduction

```sh
refs/scripts/build_olmsmoother2_cli.sh
python3 refs/scripts/smoke_olmsmoother2_pf8_host_adapter_chain_20260718.py
```

## Claims Not Made

- No Mac AE exactness.
- No claim that the diagnostic environment gate is a permanent host policy.
- No claim that the post-first-append live Windows polygon is known.
