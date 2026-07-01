# OLMDistanceGradation case_0023 Probe Refresh - 2026-07-01

Fresh single-case Mac AE rerun of the remaining
`olmdistancegradation_extended__case_0023` witness lane, using a materialized
single-case request plus a parser-backed field debug report.

## Materialized request

- request dir:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701`
- plan:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/OLMDG_CASE0023_PROBE_PLAN.json`

## Live run

- command:
  `python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701 --case-id olmdistancegradation_extended__case_0023 --output-dir /tmp/olmdg_case0023_probe_20260701 --ae-env OLM_DG_DEBUG_DUMP_PATH=/tmp/olmdg_case0023_probe_20260701/field_debug.txt --ae-env 'OLM_DG_DEBUG_POINTS=1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394'`
- parser:
  `python3 scripts/analyze_distancegradation_debug_points.py --debug-log /tmp/olmdg_case0023_probe_20260701/field_debug.txt --output-json handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/field_debug_report.json --output-md handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/field_debug_report.md`

## High-signal refresh facts

- The refreshed run reproduces the same two live buckets as the 2026-06-30
  note:
  1. the `inside EDT = 1.0` edge witnesses at `(1699,7)` and `(1698,7)`
  2. the threshold/plateau witnesses around `(415,393)`
- Fresh field debug still shows the edge family is already decided before
  compose/writeback:
  - `(1699,7)` -> `field_x=0`, `raw_inside=1`, `raw_outside=0`
  - `(1700,7)` -> `field_x=1`, `raw_inside=0`, `raw_outside=1`
- Fresh field debug also still shows the threshold family straddling the
  `Inside Threshold = 36` boundary:
  - `(414,393)` -> `field_x=0`, `raw_inside=35.0142822`
  - `(415,393)` -> `field_x=1`, `raw_inside=36.0138855`
  - `(416,393)` -> `field_x=1`, `raw_inside=37.0135117`

## Why this matters

- This rerun does not change the core conclusion, but it upgrades the workflow:
  `case_0023` is now reproducible through a dedicated single-case request and a
  machine-readable point parser, not only through an older one-off note.
- That makes future witness checks safer:
  any new source patch in `dt_to_normalized()` / `build_distance_field()` can be
  rechecked against the same live points without reconstructing the setup.

## Artifact paths

- Parsed report:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/field_debug_report.md`
- Parsed report JSON:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_distancegradation_case0023_probe_20260701/field_debug_report.json`
