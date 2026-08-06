# OLMSmoother2 typed center actual-AEX/production boundary

Verdict: `PASS_ACTUAL_AEX_TO_PRODUCTION_TYPED_CENTER_EXACT`

The unchanged Windows AEX typed worker and production `RenderBits` emit identical raw ARGB storage for a 1x1 v1 center-sample fixture.

| Depth | Actual AEX | Production |
| --- | --- | --- |
| PF16 | `0050cd0f00403370` | `0050cd0f00403370` |
| PF32 | `0000203fded6fc3d0000003f2365603f` | `0000203fded6fc3d0000003f2365603f` |

## Evidence boundary

This directly closes the previously oracle-mediated PF16/PF32 typed-store connection only for the declared 1x1 center fixture. It does not broaden the existing AE-exact case suites.

## Reproduction

```sh
python3 tools/emulation/test_olmsmoother2_typed_center_production_actual_aex_20260805.py
```
