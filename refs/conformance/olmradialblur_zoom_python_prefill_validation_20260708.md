# OLMRadialBlur Zoom Python Prefill Validation

Date: 2026-07-08

## Verdict

Reduced-geometry validation result: `exact_reduced_geometry_prefill_match`.

- Case: `case_0009`
- XY: `[6, 0]`
- Mode: `--direct-debug-size 32x32`, default debug quality step `90.0`, stop at `0x180005ba2` before `FUN_18000b150` / `FUN_18000a9d0`.
- Max absolute difference across compared cells: `0.0`

## Commands

```bash
python3 tools/emulation/test_zoom_case0009.py --direct-zoom-core --direct-debug-size 32x32 --direct-stop-after-prefill --max-instructions 2000000 --output-json refs/reports/olmradialblur_zoom_debug32_original_prefill_stop_20260708.json --output-md refs/reports/olmradialblur_zoom_debug32_original_prefill_stop_20260708.md
python3 tools/emulation/test_zoom_case0009.py --direct-zoom-core --direct-debug-size 32x32 --direct-python-prefill --direct-stop-after-prefill --max-instructions 2000000 --output-json refs/reports/olmradialblur_zoom_debug32_python_prefill_stop_20260708.json --output-md refs/reports/olmradialblur_zoom_debug32_python_prefill_stop_20260708.md
```

## Facts

- Original AEX prefill stop classification: `direct-original-prefill-stop-witness`
- Python prefill stop classification: `direct-python-prefill-stop-candidate`
- Original instructions: `85934`
- Python prefill instructions: `24956`
- Geometry original: `{'angle_count': 4, 'angle_index': 3.557459233642021, 'angle_raw': 3.656665325164795, 'angle_step': 0.003490658476948738, 'height': 1080, 'max_radius_plus': 1103, 'min_radius': 1055, 'quality_step': 90.0, 'radial_count': 49, 'radius_index': 41.22802734375, 'radius_raw': 1096.22802734375, 'width': 1920}`
- Geometry python: `{'angle_count': 4, 'angle_index': 3.557459233642021, 'angle_raw': 3.656665325164795, 'angle_step': 0.003490658476948738, 'height': 1080, 'max_radius_plus': 1103, 'min_radius': 1055, 'quality_step': 90.0, 'radial_count': 49, 'radius_index': 41.22802734375, 'radius_raw': 1096.22802734375, 'width': 1920}`

## Compared Cells

| Group | Cell | Original | Python | max_abs_diff |
| --- | --- | --- | --- | --- |
| `final_7` | `a0_r0` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `0.0` |
| `final_7` | `a0_r1` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `0.0` |
| `final_7` | `a1_r0` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `0.0` |
| `final_7` | `a1_r1` | `[0.0, 0.0, 0.0, 1.0]` | `[0.0, 0.0, 0.0, 1.0]` | `0.0` |
| `denom_0x843` | `a0_r0` | `0.0` | `0.0` | `0.0` |
| `denom_0x843` | `a0_r1` | `0.0` | `0.0` | `0.0` |
| `denom_0x843` | `a1_r0` | `0.0` | `0.0` | `0.0` |
| `denom_0x843` | `a1_r1` | `0.0` | `0.0` | `0.0` |
| `accum_0x842` | `a0_r0` | `[0.0, 0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 0.0]` | `0.0` |
| `accum_0x842` | `a0_r1` | `[0.0, 0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 0.0]` | `0.0` |
| `accum_0x842` | `a1_r0` | `[0.0, 0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 0.0]` | `0.0` |
| `accum_0x842` | `a1_r1` | `[0.0, 0.0, 0.0, 0.0]` | `[0.0, 0.0, 0.0, 0.0]` | `0.0` |

## Interpretation

This validates the Python prefill against the original AEX prefill for the reduced `32x32/q90` direct-core geometry at the exact pre-worker boundary. It does not yet prove full-size semantics, but it removes the most immediate concern that the Python repeat-border prefill formula is merely synthetic or structurally unrelated to the AEX loop.

The full-size `case_0009` Python prefill candidate remains a candidate until validated by either full-size original AEX prefill completion, Windows final-plane cell traces, or one-worker-at-a-time removal of the `b150/a9d0` detours.
