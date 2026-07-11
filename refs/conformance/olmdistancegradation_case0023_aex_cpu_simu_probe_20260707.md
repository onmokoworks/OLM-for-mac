# OLMDistanceGradation case_0023 AEX CPU simu probe - 2026-07-07

## Summary

This note records the first case-bound `FUN_181174760` direct-call probes using
the Windows `DistanceGradation.aex` CPU code on macOS through
`tools/emulation/test_dg_fieldgen_p1b.py`.

The probe now accepts a real `before_effects` PNG, derives the binary mask from
RGBA alpha, crops it, calls the AEX field-generation helper, and samples witness
points from the resulting float field.

Later the same harness gained the limited `cvNormalize` / `NORM_MINMAX` detour
and can run full-frame case_0023 inside/outside field-helper passes.

## FACT

- AEX function: `FUN_181174760` at `0x181174760`
- AEX path: `plugins_2025/DistanceGradation.aex`
- Source PNG:
  `refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png`
- Mask source: alpha channel, nonzero alpha -> `255`, zero alpha -> `0`
- Case params used by the direct helper call:
  - `threshold = 36`
  - `param8 = 1`
- The helper call completed in both real-PNG crop probes.
- Both probes hit:
  - `FUN_1812aef70` twice
  - `FUN_18117ca50` once
  - OpenCV detours: `cv::dist_transform` once, `cv::resize_same_shape` twice,
    `cv::threshold` once
- After the P2 normalize detour, full-frame probes also hit
  `cv::normalize_minmax` once and avoid emulating the final OpenCV normalize
  body.

## Full-frame inside/outside result

- Combined JSON:
  `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`
- Inside run:
  `tools/emulation/run_outputs/dg_fieldgen_case0023_fullframe_alpha_inside_20260707.json`
- Outside run:
  `tools/emulation/run_outputs/dg_fieldgen_case0023_fullframe_alpha_outside_20260707.json`
- Source PNG:
  `refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png`
- Inside pass: alpha mask, `threshold=36`, `param8=1`
- Outside pass: inverted alpha mask, `threshold=0`, `param8=1`
- Both combine at sampled binary fields: `min(inside + outside, 1)`

| XY | Inside mask | Inside field | Outside mask | Outside field | Both field |
| --- | ---: | ---: | ---: | ---: | ---: |
| `(1698,7)` | `255` | `0.0` | `0` | `0.0` | `0.0` |
| `(1699,7)` | `255` | `0.0` | `0` | `0.0` | `0.0` |
| `(1700,7)` | `0` | `0.0` | `255` | `1.0` | `1.0` |
| `(1699,6)` | `0` | `0.0` | `255` | `1.0` | `1.0` |
| `(1699,8)` | `255` | `0.0` | `0` | `0.0` | `0.0` |
| `(414,393)` | `255` | `0.0` | `0` | `0.0` | `0.0` |
| `(415,393)` | `255` | `1.0` | `0` | `0.0` | `1.0` |
| `(416,393)` | `255` | `1.0` | `0` | `0.0` | `1.0` |
| `(415,392)` | `255` | `0.0` | `0` | `0.0` | `0.0` |
| `(415,394)` | `255` | `1.0` | `0` | `0.0` | `1.0` |

Reading: the AEX CPU helper's full-frame field at the live edge witness
`(1699,7)` is `0.0` after Both add-saturate. With the case_0023 compose/invert
semantics, this maps to the blue Gradation endpoint, matching the current
Mac-side field/debug behavior rather than the red endpoint in the older
reference PNG.

## Threshold-family crop result

- Output JSON:
  `tools/emulation/run_outputs/dg_fieldgen_case0023_threshold_crop_20260707.json`
- Crop: `x=380, y=350, w=96, h=96`
- Instructions: `68743`
- Output range: `0.0 .. 1.0`

| XY | Mask | AEX field output |
| --- | ---: | ---: |
| `(414,393)` | `255` | `0.0` |
| `(415,393)` | `255` | `1.0` |
| `(416,393)` | `255` | `1.0` |
| `(415,392)` | `255` | `0.0` |
| `(415,394)` | `255` | `1.0` |

This reproduces the already documented threshold-family field pattern from
`refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json`
and the live Mac debug dump: `0, 1, 1` across `(414,393)`, `(415,393)`,
`(416,393)`.

## Edge-family crop result

- Output JSON:
  `tools/emulation/run_outputs/dg_fieldgen_case0023_edge_crop_20260707.json`
- Crop: `x=1688, y=0, w=32, h=24`
- Instructions: `14841`
- Output range: `0.0 .. 0.0`

| XY | Mask | AEX field output |
| --- | ---: | ---: |
| `(1698,7)` | `255` | `0.0` |
| `(1699,7)` | `255` | `0.0` |
| `(1700,7)` | `0` | `0.0` |
| `(1699,6)` | `0` | `0.0` |
| `(1699,8)` | `255` | `0.0` |

## INFERENCE / Boundary

- The threshold-family crop is useful evidence that the AEX CPU helper, when
  driven from the current recapture alpha mask, agrees with the Mac-side
  field-debug classification at the threshold triplet.
- The older edge-family crop is only a smoke/probe because cropping changes the
  Euclidean distance field. The full-frame inside/outside result above is the
  stronger field-helper evidence.
- This still does not prove whole-plugin Mac AE exact. It proves the Windows CPU
  AEX field-helper lane agrees with the Mac-side value at the sampled edge
  witness, strengthening the reference-path split classification.

## Commands

```bash
tools/emulation/.venv/bin/python -m py_compile tools/emulation/test_dg_fieldgen_p1b.py
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py --mask-png refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png --mask-channel alpha --crop 380,350,96,96 --points '414,393;415,393;416,393;415,392;415,394' --points-global --threshold 36 --param8 1
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py --mask-png refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png --mask-channel alpha --crop 1688,0,32,24 --points '1698,7;1699,7;1700,7;1699,6;1699,8' --points-global --threshold 36 --param8 1
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py --mask-png refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png --mask-channel alpha --points '1698,7;1699,7;1700,7;1699,6;1699,8;414,393;415,393;416,393;415,392;415,394' --threshold 36 --param8 1
tools/emulation/.venv/bin/python tools/emulation/test_dg_fieldgen_p1b.py --mask-png refs/win_references/olm_return_20260706/DistanceGradation/olmdistancegradation_case0023_current_aex_recapture_20260702__software_16bpc__fr24__olmdistancegradation_extended__case_0023_current_aex_before_effects.png --mask-channel alpha --invert-mask --points '1698,7;1699,7;1700,7;1699,6;1699,8;414,393;415,393;416,393;415,392;415,394' --threshold 0 --param8 1
```
