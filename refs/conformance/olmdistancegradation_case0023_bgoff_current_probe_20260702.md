# OLMDistanceGradation case_0023 bg_off Current Probe - 2026-07-02

- Status: `upstream-field-ownership-still-live`
- Live Mac bg_off rerun:
  [refs/reports/ae_single_case_distancegradation_case0023_bgoff_live_20260702/AE_SINGLE_CASE_RESULT.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/ae_single_case_distancegradation_case0023_bgoff_live_20260702/AE_SINGLE_CASE_RESULT.json)
- Windows bg_off reference:
  [bg_off reference PNG](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/win_references/olmdistancegradation_16bpc_bg_compose_variants_20260626/DistanceGradation/renders/olmdistancegradation_16bpc_bg_compose_variants_20260626__software_16bpc__fr24__olmdistancegradation_case_0023_bg_off_variant.png)

## Result

Current Mac `Use Background Color=0` still differs from the Windows `bg_off`
reference by exactly `73px` (`max_diff=255`, `mean_diff=0.004585382908950617`).

That matters because it means the remaining `case_0023` lane is not only a
`use_bg=1` compose blend problem. The same sparse residual survives with
background disabled.

## Representative witnesses

Agrees:

- `(1698,7)` -> gradation-color opaque on both
- `(1700,7)` -> transparent on both
- `(414,393)` -> gradation-color opaque on both
- `(416,393)` -> transparent on both

Still disagrees:

- `(1699,7)` -> live Mac bg_off stays gradation-color opaque, Windows bg_off is transparent
- `(415,393)` -> live Mac bg_off is transparent, Windows bg_off stays gradation-color opaque

## Interpretation

This is good negative evidence:

- the active residual is still upstream of just the `use_bg=1` final blend
- the Mac field ownership / threshold staging lane is still live
- but the disagreement is now more localized than a broad branch failure,
  because neighboring representative points already match on both the edge and
  threshold families

## Practical consequence

- Keep the threshold-family `(415,393)` `use_bg=1` mismatch in provenance/export
  classification unless a current Windows export contradicts it.
- Keep the surviving edge-family / bg_off-localized witness mismatch
  (`1699,7`) as a live implementation lane.
- Do not reopen broad compose-writeback tuning from this probe alone.
