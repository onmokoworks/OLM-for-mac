# OLMDistanceGradation 0010/0011 R/A quantization probe

Date: 2026-07-09

## Decision

`case_0010/0011` are not RGB-color bugs. The visible R/A `±2` PNG deltas are
consistent with a one-word `PF_Pixel16` alpha-store difference that AE/export
then exposes as `2 * store_a - 1` in the rendered PNG. Because the sign flips
between witness pixels, this should not be fixed with a global store rounding
toggle. Treat it as a narrow distance-field float/normalization or PF16
store-boundary lane.

## Evidence

Commands:

```sh
python3 scripts/run_ae_single_case.py \
  --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625 \
  --case-id olmdistancegradation_extended__case_0010 \
  --output-dir refs/reports/ae_single_case_olmdistancegradation_0010_ra_field_debug_20260709 \
  --ae-env "OLM_DG_DEBUG_DUMP_PATH=.../field_debug.txt" \
  --ae-env "OLM_DG_SHADE_DEBUG_PATH=.../shade_debug.txt" \
  --ae-env "OLM_DG_DEBUG_POINTS=6,40;901,394;1018,394"

python3 scripts/run_ae_single_case.py \
  --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625 \
  --case-id olmdistancegradation_extended__case_0011 \
  --output-dir refs/reports/ae_single_case_olmdistancegradation_0011_ra_field_debug_20260709_retry2 \
  --ae-env "OLM_DG_DEBUG_DUMP_PATH=.../field_debug.txt" \
  --ae-env "OLM_DG_SHADE_DEBUG_PATH=.../shade_debug.txt" \
  --ae-env "OLM_DG_DEBUG_POINTS=915,392;1004,392;912,393"
```

### Witnesses

| case | xy | field_x | out_a | Mac store_a | Mac PNG R/A | Windows PNG R/A | implied Windows store_a | classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0010 | `(6,40)` | `0.900283873` | `0.0997161269` | `3267` | `6533` | `6535` | `3268` | Mac store -1 |
| 0010 | `(901,394)` | `0.69859308` | `0.30140692` | `9877` | `19753` | `19751` | `9876` | Mac store +1 |
| 0010 | `(1018,394)` | `0.69859308` | `0.30140692` | `9877` | `19753` | `19751` | `9876` | Mac store +1 |
| 0011 | `(915,392)` | `0.134536773` | `0.865463257` | `28360` | `56719` | `56717` | `28359` | Mac store +1 |
| 0011 | `(1004,392)` | `0.134536773` | `0.865463257` | `28360` | `56719` | `56717` | `28359` | Mac store +1 |
| 0011 | `(912,393)` | `0.134536773` | `0.865463257` | `28360` | `56719` | `56717` | `28359` | Mac store +1 |

Relevant debug excerpts:

```text
0010 (6,40): raw_outside=41 outside_x=0.900283873 out_a=0.0997161269 store_a=3267
0010 (901,394): raw_inside=44.011364 inside_x=0.69859308 out_a=0.30140692 store_a=9877
0011 (915,392): raw_inside=46.8187981 inside_x=0.134536773 out_a=0.865463257 store_a=28360
```

The plugin stores `store_r=32768` for these Render Mode=Gradation Color,
no-background points, but the PNG R channel follows the exported alpha-sized
visible value. Therefore R and A deltas are the same symptom.

## Next

Do not change global `clamp16()` rounding from this evidence. The required
next proof is one of:

- local: compare the exact normalized distance formula / denominator for these
  witness raw distances against OpenCV 4.5.5 behavior, including float
  precision and final field-world packing;
- external: a same-run Windows witness for one negative and one positive point
  that captures raw distance, normalized field word, compose `out_a`, and
  `PF_Pixel16` store word before export.
