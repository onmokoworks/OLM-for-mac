# OLMDistanceGradation 16bpc case_0023 Point Debug - 2026-06-30

Live Mac AE point-debug for the remaining Constant `In/Out=Both` +
`Outside Threshold=0` witness family.

Source run:

- `/tmp/olmdg_case0023_pointdebug_20260630_multi/field_debug.txt`
- `python3 scripts/run_ae_single_case.py --request-dir handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625 --case-id olmdistancegradation_extended__case_0023 --output-dir /tmp/olmdg_case0023_pointdebug_20260630_multi --ae-env 'OLM_DG_DEBUG_DUMP_PATH=/tmp/olmdg_case0023_pointdebug_20260630_multi/field_debug.txt' --ae-env 'OLM_DG_DEBUG_POINTS=1699,7;1698,7;1700,7;1699,6;1699,8;415,393;414,393;416,393;415,392;415,394'`

## Witness groups

### Bucket A: inside EDT `1.0`

- `point x=1699 y=7 alpha=0.00393676758 d_alpha=1 field_x=0 raw_inside=1 raw_outside=0`
- `point x=1698 y=7 alpha=0.0274658203 d_alpha=1 field_x=0 raw_inside=1 raw_outside=0`
- Neighboring outside-side points flip immediately:
  - `point x=1700 y=7 alpha=0 d_alpha=0 field_x=1 raw_inside=0 raw_outside=1`
  - `point x=1699 y=6 alpha=0 d_alpha=0 field_x=1 raw_inside=0 raw_outside=1`
- One nearby diagonal stays in the inside family:
  - `point x=1699 y=8 alpha=0.756866455 d_alpha=1 field_x=0 raw_inside=1.41421354 raw_outside=0`

Reading:

- The active wrong `inside EDT = 1.0` witness is already decided in field prep:
  Mac has `field_x=0` and `d_alpha=1` at the tracked bad pixels, while the
  adjacent outside-side neighbors already sit on `field_x=1` / `d_alpha=0`.
- This is not a final writeback artifact. The endpoint split is present before
  the final 16bpc color store.

### Bucket B: inside EDT `36.013885...`

- `point x=415 y=393 alpha=1 d_alpha=1 field_x=1 raw_inside=36.0138855 raw_outside=0`
- Nearby neighbors straddle the threshold exactly as the residual split
  predicted:
  - `point x=414 y=393 alpha=1 d_alpha=1 field_x=0 raw_inside=35.0142822 raw_outside=0`
  - `point x=416 y=393 alpha=1 d_alpha=1 field_x=1 raw_inside=37.0135117 raw_outside=0`
  - `point x=415 y=392 alpha=1 d_alpha=1 field_x=0 raw_inside=35.9026451 raw_outside=0`
  - `point x=415 y=394 alpha=1 d_alpha=1 field_x=1 raw_inside=36.0555115 raw_outside=0`

Reading:

- The second residual bucket is a pure threshold-ownership witness around
  `Inside Threshold = 36`.
- The field flips between `field_x=0` and `field_x=1` across neighbors whose
  raw inside distance straddles `36`, so the unresolved lane is still an
  upstream Constant helper plateau/ownership rule.

## Bottom line

- `case_0023` is now grounded by live Mac AE field witnesses, not just PNG
  residual shape.
- Both surviving buckets are upstream field/threshold decisions.
- The remaining work should stay on Constant helper staging / threshold
  ownership for `Both + Outside Threshold=0`, not on compose or writeback.
