# 16bpc Mac AE Rerun - 2026-06-26 20:49 JST

Local Mac AE rerun of the 16bpc validation bundle.

- After Effects: local Mac AE 2026
- Requests:
  `handoffs/ae_host_validation/20260625_221356_16bpc_mac_ae_validation/`
- Render script:
  `scripts/ae_pixel_validation_render.jsx`
- Verification batch:
  `refs/reports/ae_pixel_validation_16bpc_mac_20260626_204952_rerun/`

## Host Notes

- The `osascript ... DoScriptFile` wrapper hit AppleEvent timeout `-1712`,
  but the AE host continued rendering and wrote the candidate PNGs.
- The rerun artifacts were copied from `/tmp/olm_ae_pixel_batch_20260626_macae_rerun`
  into `refs/reports/ae_pixel_validation_16bpc_mac_20260626_204952_rerun/`.

## Exact Counts

- `OLMBlur`: 0/7 exact
- `OLMColorKey`: 8/9 exact
- `OLMDistanceGradation basic`: 8/12 exact
- `OLMDistanceGradation blur`: 0/1 exact
- `OLMDistanceGradation extended`: 1/16 exact

## Key Observations

### OLMBlur

- Non-Legacy failing channels are confined to cyclic deltas
  `-513`, `-512`, `+512`, `+513`.
- `olmblur__case_0003` and `olmblur__case_0004` reduce further to pure
  `+/-512`.
- `olmblur__case_0007` adds a separate `32513` cyclic anomaly on top of the
  `+/-512` family, consistent with a Legacy-only border/seed problem.
- Interpretation: do not tune blur kernel/radius math from these 16bpc
  residuals yet. The active target is writeback/export grounding.

### OLMColorKey

- Only `olmcolorkey__case_0009` remains non-exact.
- Residual polarity is unchanged: `12597px` differ, all in the
  `candidate kept / Windows removed` direction.
- This matches the focused report in
  `refs/conformance/olmcolorkey_16bpc_case_0009_analysis.md`.

### OLMDistanceGradation

- Basic remaining failures stay concentrated in non-all-opaque / non-no-source
  cases:
  `case_0015`, `0017`, `0018`, `0019`.
- Extended failures split into at least three visible families:
  1. `case_0010..0016`: structured ramp mismatch near edges and thresholds.
  2. `case_0020..0023`: repeated red/blue palette swap witnesses such as
     candidate `[65535,0,0,65535]` vs reference `[6940,0,60910,65535]`.
  3. `case_0027/0028`: candidate RGB zeroed with alpha preserved, while the
     reference keeps a nonzero red ramp.
- Interpretation: the next DistanceGradation proof should focus on 16bpc
  compose/render-mode/background-color behavior before changing blur or
  interpolation math broadly.
