# OLMKiraKira Hotspot Neighborhood Probe - 2026-07-01

Live Mac AE 8bpc neighborhood probe for the residual hotspot case
`kk_vertical_len50_brightness1_strength100`.

This note now includes both:

- the initial `3x3` probe around `(934,118)`
- a follow-up `5x5` probe that checks whether the apparent local plateau
  extends farther right/down

Prepared request:

- request dir:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701`
- debug plan:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701/KIRAKIRA_HOTSPOT_PROBE_PLAN.json`

Live run:

- command:
  `python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701 --case-id kk_vertical_len50_brightness1_strength100 --output-dir /tmp/kirakira_hotspot_probe_20260701 --ae-env OLMKIRAKIRA_DEBUG_DUMP_PATH=/tmp/kirakira_hotspot_probe_20260701/kirakira_debug.log --ae-env 'OLMKIRAKIRA_DEBUG_POINTS=933,117;934,117;935,117;933,118;934,118;935,118;933,119;934,119;935,119'`
- neighborhood analysis:
  `python3 scripts/analyze_kirakira_compose_debug_neighborhood.py --debug-log /tmp/kirakira_hotspot_probe_20260701/kirakira_debug.log --center 934,118 --radius 1 --windows-target-u8 131 --output-json handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701/kirakira_neighborhood.json --output-md handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701/kirakira_neighborhood.md`

5x5 follow-up:

- request dir:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701_r2`
- command:
  `python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701_r2 --case-id kk_vertical_len50_brightness1_strength100 --output-dir /tmp/kirakira_hotspot_probe_20260701_r2 --ae-env OLMKIRAKIRA_DEBUG_DUMP_PATH=/tmp/kirakira_hotspot_probe_20260701_r2/kirakira_debug.log --ae-env 'OLMKIRAKIRA_DEBUG_POINTS=932,116;933,116;934,116;935,116;936,116;932,117;933,117;934,117;935,117;936,117;932,118;933,118;934,118;935,118;936,118;932,119;933,119;934,119;935,119;936,119;932,120;933,120;934,120;935,120;936,120'`
- neighborhood analysis:
  `python3 scripts/analyze_kirakira_compose_debug_neighborhood.py --debug-log /tmp/kirakira_hotspot_probe_20260701_r2/kirakira_debug.log --center 934,118 --radius 2 --windows-target-u8 131 --output-json handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701_r2/kirakira_neighborhood.json --output-md handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701_r2/kirakira_neighborhood.md`

## Primary local facts

- Center `(934,118)` remains the known Mac hotspot witness:
  - `glow_alpha_after_opacity = 0.507505655`
  - `out_u8 = [144,144,144,255]`
  - Windows target byte remains `131`
- On the same gray-source row (`src_u8 = [30,30,30]`):
  - `(933,118)` drops to `alpha=0.424754471`, `R=126`
  - `(934,118)` and `(935,118)` stay flat at `alpha=0.507505655`, `R=144`
- On the next gray-source row:
  - `(933,119)` stays low at `alpha=0.419824570`, `R=124`
  - `(934,119)` and `(935,119)` again stay almost flat at `alpha=0.505595922`, `R=144`
- The upper row uses a brighter source (`src_u8 = [139,139,139]`), but still
  shows the same left-edge split:
  - `(933,117)` is lower at `alpha=0.429701477`, `R=189`
  - `(934,117)` and `(935,117)` stay flat at `alpha=0.509453773`, `R=198`

## Reading

- This 3x3 probe does not look like a smooth center-out attenuation around the
  hotspot. It looks like a piecewise boundary:
  - left neighbor column `x=933` is consistently lower
  - `x=934..935` forms a near-plateau on all three sampled rows
- The center mismatch to Windows is still `144 -> 131`, but the local shape now
  suggests that the live Mac path already contains a branch-like or region-like
  decision before final writeback, not just a scalar final-byte rounding issue.
- That makes the pending Windows witness even more valuable:
  the key question is no longer "is there some broad compose gain drift?" but
  "which stage produces the `x=933` vs `x>=934` split, and does Windows apply a
  different hotspot-local attenuation on the plateau itself?"

## 5x5 confirmation

The wider probe strengthens that reading rather than weakening it.

- At `y=118..120` with the same gray source (`src_u8 = [30,30,30]`):
  - `x=932` is the low lane: `R = 107, 105, 103`
  - `x=933` is the transition lane: `R = 126, 124, 123`
  - `x=934..936` is the plateau lane: `R = 144, 144, 144` and then
    `143,143,143` on the lowest sampled row
- On the brighter rows above:
  - `x=932` and `x=933` are still the lower lanes
  - `x=934..936` again stay flat together at `198` or `252`
- The alpha values follow the same pattern:
  - `x=932` is always lowest
  - `x=933` is intermediate
  - `x=934..936` are nearly identical within each row

So the live Mac shape is not just "center pixel too bright".
It is a three-lane local structure:

1. a low left lane at `x=932`
2. a transition lane at `x=933`
3. a broad plateau at `x>=934`

That makes the most useful Windows witness question even narrower:
does Windows keep the same lane split but apply a stronger attenuation on the
plateau, or does the lane split itself differ before compose/writeback?

## Artifact paths

- Raw debug log: `/tmp/kirakira_hotspot_probe_20260701/kirakira_debug.log`
- Parsed neighborhood JSON:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701/kirakira_neighborhood.json`
- Parsed neighborhood Markdown:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701/kirakira_neighborhood.md`
- 5x5 parsed neighborhood Markdown:
  `handoff/ae_pixel_validation_20260618/requests/ae_single_kirakira_hotspot_probe_20260701_r2/kirakira_neighborhood.md`
