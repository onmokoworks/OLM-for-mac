# OLMDistanceGradation Depth-gate Near-miss Family - 2026-07-08

Source evidence:

- Primary depth-gate report: `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`
- Candidate renders: `/tmp/olmdg_16ext_depthgate2`
- Reference manifest: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/reference_manifest.json`

## FACT

The depth-gated build closes `case_0023` and leaves a new `max=1` family in `case_0024..0027`.
The values below were recomputed from the candidate and expected PNGs with RGBA int64 absolute diffs.

| Case | Nonzero px | Max | BBox `(x0,y0)-(x1,y1)` | Channel counts `(R,G,B,A)` |
| --- | ---: | ---: | --- | --- |
| `case_0024` | `3984` | `1` | `(232,328)-(1919,1079)` | `(2934,0,1050,0)` |
| `case_0025` | `12291` | `1` | `(0,0)-(1919,1079)` | `(3143,0,9148,0)` |
| `case_0026` | `2570` | `1` | `(265,222)-(1893,1019)` | `(1216,0,1354,0)` |
| `case_0027` | `489` | `1` | `(390,443)-(1893,941)` | `(442,13,40,0)` |

Shared parameters:

- `In/Out=3`
- `Inside Threshold=158`
- `Use Background Color=1`
- `Gradation Color=[0.1098041459918,0,0.93333333730698,1]`
- `BG Color=[1,0,0,1]`
- `Blur Mode=1`
- `Blur Size=0`

Parameter splits:

| Case | Invert | Outside Threshold | Render Mode | Interpolation Mode | Power |
| --- | ---: | ---: | ---: | ---: | ---: |
| `case_0024` | `0` | `17` | `1` | `3` | `1` |
| `case_0025` | `1` | `13` | `1` | `3` | `1` |
| `case_0026` | `1` | `13` | `1` | `4` | `2.59740734100342` |
| `case_0027` | `1` | `13` | `2` | `4` | `2.59740734100342` |

## INFERENCE

- This is a coherent near-miss family: the shared `In/Out=3`, BG-enabled red/purple palette, and contour-shaped diffs point at a quantization or interpolation/render-mode boundary rather than four unrelated bugs.
- `case_0025` appears to add a framewide low-level blue-channel peppering on top of the contour residual, so it is less clean as a first witness.
- `case_0026` and `case_0027` are the cleanest pair: they share all listed parameters except `Render Mode` (`1 -> 2`), and `case_0026` still has enough residual pixels to inspect.

## Next Witness

Use `case_0026` first, with `case_0027` as the paired control. The first witness should collect representative `max=1` pixels from contour regions and compare field value, interpolation input/output, render-mode branch, and final 16bpc store. Do not use the AE-free CLI reimplementation as Windows-reference truth for this lane.
