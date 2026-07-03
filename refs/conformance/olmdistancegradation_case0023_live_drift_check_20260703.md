# OLMDistanceGradation case_0023 Live Drift Check - 2026-07-03

Status: `stable-live-witness-repeat`

This was a bounded Mac AE rerun of `olmdistancegradation_extended__case_0023`
using the existing single-case probe request in both:

- `Use Background Color = 1`
- `Use Background Color = 0`

Outputs:

- [bg_on result](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_distancegradation_case0023_live_20260703_bg_on/AE_SINGLE_CASE_RESULT.json)
- [bg_off result](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_distancegradation_case0023_live_20260703_bg_off/AE_SINGLE_CASE_RESULT.json)

## Witness repeat

The six primary witness pixels are byte-identical to the 2026-07-02 live reruns.

### bg_on

- `(1698,7)` -> `[28,0,238,255]`
- `(1699,7)` -> `[28,0,238,255]`
- `(1700,7)` -> `[255,0,0,255]`
- `(414,393)` -> `[28,0,238,255]`
- `(415,393)` -> `[255,0,0,255]`
- `(416,393)` -> `[255,0,0,255]`

### bg_off

- `(1698,7)` -> `[28,0,238,255]`
- `(1699,7)` -> `[28,0,238,255]`
- `(1700,7)` -> `[0,0,0,0]`
- `(414,393)` -> `[28,0,238,255]`
- `(415,393)` -> `[0,0,0,0]`
- `(416,393)` -> `[0,0,0,0]`

## Field debug repeat

Both runs repeat the same threshold crossing and edge-family ownership facts:

- `(414,393)` -> `raw_inside=35.0142822`, `field_x=0`
- `(415,393)` -> `raw_inside=36.0138855`, `field_x=1`
- `(416,393)` -> `raw_inside=37.0135117`, `field_x=1`
- `(1699,7)` remains `field_x=0`
- `(1700,7)` remains `field_x=1`

## Interpretation

This does not close the lane, but it does freeze one useful operational fact:

- the current Mac AE live witness surface for `case_0023` is stable across
  repeated runs
- the threshold-family provenance split remains stable
- the edge-family mismatch remains live and is not a one-off host drift

So the next meaningful external evidence is still:

- current Windows Software export provenance for `case_0023`, and/or
- stronger edge-family typed output-word / refcon witness data

not another broad local threshold rewrite.
