# OLMKiraKira Compose Boundary Mac Witness - 2026-06-30

Live Mac AE 8bpc witness capture for the single-ray Software case
`kk_vertical_len50_brightness1_strength100`.

Source run:

- request dir: `/tmp/ae_kirakira_single_ray_request_20260630`
- output dir: `/tmp/kirakira_compose_debug_20260630_8bpc`
- command:
  `python3 scripts/run_ae_single_case.py --request-dir /tmp/ae_kirakira_single_ray_request_20260630 --case-id kk_vertical_len50_brightness1_strength100 --output-dir /tmp/kirakira_compose_debug_20260630_8bpc --ae-env 'OLMKIRAKIRA_DEBUG_DUMP_PATH=/tmp/kirakira_compose_debug_20260630_8bpc/kirakira_debug.log' --ae-env 'OLMKIRAKIRA_DEBUG_POINTS=934,118;960,540;960,490;1010,540'`

## Witness values

### Primary residual hotspot `(934,118)`

- `src=(0.117647059, 0.117647059, 0.117647059, 1)`
- `glow_norm=(1, 1, 1, 0.507505655)`
- `glow_alpha_after_opacity=0.507505655`
- `out_prequantized=(0.565446138, 0.565446138, 0.565446138, 1)`
- `out_u8=(144,144,144,255)`
- Saved PNG candidate: `[144,144,144,255]`
- Windows reference PNG: `[131,131,131,255]`

Reading:

- The Mac plug-in's internal compose output at the primary hotspot already
  matches its saved PNG byte exactly.
- Therefore this hotspot is not a "final PNG export only" or "last-byte only"
  discrepancy on the Mac side. The divergence is already present at the plugin
  compose boundary.

### Control witnesses from the existing Windows fd90 package

- Center `(960,540)`:
  - Mac debug `glow_alpha_after_opacity=0.440345466`
  - Mac debug `out_u8=(129,129,129,255)`
  - Saved PNG candidate `[129,129,129,255]`
  - Windows reference `[124,124,124,255]`
- Up `(960,490)`:
  - Mac debug `glow_alpha_after_opacity=0.467837244`
  - Mac debug `out_u8=(242,231,151,255)`
  - Saved PNG candidate `[242,231,151,255]`
  - Windows reference `[240,229,144,255]`
- Right `(1010,540)`:
  - Mac debug `glow_alpha_after_opacity=0.438375115`
  - Mac debug `out_u8=(129,129,129,255)`
  - Saved PNG candidate `[129,129,129,255]`
  - Windows reference `[123,123,123,255]`

Reading:

- The Mac compose-boundary dump is numerically consistent with the Mac saved
- PNGs at all checked points.
- So the remaining KiraKira lane is still upstream of any final export step
  inside AE. The unresolved branch is the internal glow/compose rule itself,
  not just post-compose byte emission.

## Bottom line

- This does not yet prove whether Windows differs in fd90 glow alpha, merge
  compose attenuation, or another immediate pre-writeback rule at the residual
  hotspot.
- It does prove that the Mac saved-PNG mismatch is already present at the
  plugin's compose boundary, so "final quantization only" is now too weak as a
  complete explanation.
- Follow-up hotspot-local diagnostic:
  `/Users/onmk/Documents/Projects/Personal/OLM as/refs/conformance/olmkirakira_hotspot_local_compose_diagnostic_20260701.md`
  computes the exact Windows-match alpha interval for `(934,118)` and shows
  that the grayscale control attenuation still projects byte `138`, so the last
  open lane is now a narrower hotspot-local attenuation/branch before
  writeback.
