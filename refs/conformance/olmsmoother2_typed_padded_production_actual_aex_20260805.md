# OLMSmoother2 padded 3x2 actual-AEX/production boundary

Verdict: `PASS_ACTUAL_AEX_TO_PRODUCTION_TYPED_PADDED_3X2_EXACT`

PF16 and PF32 use independent uniform 3x2 fixtures. Actual-AEX typed workers and production `RenderBits` agree over every pixel and preserve each row's output padding canary.

| Depth | Rowbytes | Padding/row | Compared bytes |
| --- | ---: | ---: | ---: |
| PF16 | 30 | 6 | 60 |
| PF32 | 60 | 12 | 120 |

## Boundary

This expands the center proof to padded multi-pixel traversal only. Uniform input intentionally leaves nontrivial classifier/c280 geometry unclaimed.

## Reproduction

```sh
python3 tools/emulation/test_olmsmoother2_typed_padded_production_actual_aex_20260805.py
```
