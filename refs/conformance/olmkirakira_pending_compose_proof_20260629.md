# OLMKiraKira Pending Compose Proof

## Decision Boundary

Determine whether the remaining KiraKira 8bpc Software residual comes from the internal merge-mode-1 compose site itself, from the pre-writeback float->u8 quantization/export step, or from a narrower residual hotspot not yet instrumented.

## Why Earlier Theories Stay Rejected

- BT.709 seed luma now explains the prior pass-1 upstream source-buffer mismatch.
- Ray helper stages and fd90 aggregation are already grounded within float print precision at the traced witnesses.
- The compose model audit rejects global gain or premultiplied-compose retuning as worsening total mean/max or breaking strength0 anchors.

## Grounded Up To Here

- Ray helper: `grounded-within-float-print-precision`
- BoxFilter pass1 window: `resolved and explained by BT.709 seed correction`
- fd90 aggregation witnesses: `{'center_glow_rgba': [1.0, 1.0, 1.0, 0.71891218], 'up_glow_rgba': [1.0, 1.0, 1.0, 0.76832885], 'right_glow_rgba': [1.0, 1.0, 1.0, 0.71564364]}`
- 2026-06-30 live Mac AE compose-boundary witness now proves the Mac-side
  saved-PNG mismatch is already present inside the plug-in at the compose
  boundary, not only at final AE export. On
  `kk_vertical_len50_brightness1_strength100`, hotspot `(934,118)` logs
  `src=[30,30,30]`, `glow_alpha_after_opacity=0.507505655`,
  `out_u8=[144,144,144,255]`, and the saved PNG is also `[144,144,144,255]`
  while Windows stays `[131,131,131,255]`. Controls `(960,540)`,
  `(960,490)`, and `(1010,540)` show the same boundary-vs-saved-PNG agreement.

## Missing Windows Trace Values

- Latest runtime summary: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/runtime_trace_bundle/olm_windows_action_bundle_20260629_232710_priority4_runtime_return_windows/runtime_trace_summary_kirakira_aggregation_compose_bt709_20260629_235638.json`
- compose_internal_float: `not isolated`
- pre_writeback_rgba_float: `not isolated`
- residual_hotspot_xy: `[934, 118]`
- current_trace_report: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.md`
- latest_runtime_note: `{'directly_observed_vs_inferred': {'directly_observed': ['FUN_18114fd90 entry hit at OLMKiraKira+0x114fd90 while rendering kk_vertical_len50_brightness1_strength100 Software.', 'fd90 ray pointer array at RDX contained five layer buffers; only ray0/vertical was non-zero at the requested witness pixels.', 'fd90 output buffer at stack-derived pointer 0x000002ae85ce9050; output samples read at RGBA float stride 16 bytes per pixel.', 'AE before/effect PNG-facing RGBA bytes were sampled from the rendered PNGs with System.Drawing.'], 'static_or_decomp_inferred': ['pre_normalize_rgba is inferred from the confirmed fd90 formula because only one white layer contributes: rgb_accum=alpha, alpha=ray, post-normalize rgb=1.', 'merge_mode_1_compose model remains the existing static/ref-backed aex-screen-over model, but compose internal float values were not isolated by this run.'], 'not_isolated': ['Dedicated merge-mode-1 compose internal float/writeback site after fd90.', 'Optional largest residual pixel from the included diff package; diff.json lists max_diff per case but not max-diff coordinates.']}, 'merge_mode_1_compose': {'internal_compose_float_status': 'not isolated by this breakpoint set', 'sample_inputs_outputs': [{'label': 'center', 'source_xy': [960, 540], 'source_rgba_u8': [30, 30, 30, 255], 'source_rgba_float': [0.117647058824, 0.117647058824, 0.117647058824, 1], 'glow_rgba_float': [1, 1, 1, 0.71891218], 'glow_after_opacity_rgba_float': [1, 1, 1, 0.71891218], 'composed_rgba_float': None, 'pre_writeback_rgba_float': None, 'final_writeback_or_png_rgba': [124, 124, 124, 255], 'final_png_rgba_float': [0.486274509804, 0.486274509804, 0.486274509804, 1]}, {'label': 'ray_length_up', 'source_xy': [960, 490], 'source_rgba_u8': [230, 210, 60, 255], 'source_rgba_float': [0.901960784314, 0.823529411765, 0.235294117647, 1], 'glow_rgba_float': [1, 1, 1, 0.76832885], 'glow_after_opacity_rgba_float': [1, 1, 1, 0.76832885], 'composed_rgba_float': None, 'pre_writeback_rgba_float': None, 'final_writeback_or_png_rgba': [240, 229, 144, 255], 'final_png_rgba_float': [0.941176470588, 0.898039215686, 0.564705882353, 1]}, {'label': 'ray_length_right', 'source_xy': [1010, 540], 'source_rgba_u8': [30, 30, 30, 255], 'source_rgba_float': [0.117647058824, 0.117647058824, 0.117647058824, 1], 'glow_rgba_float': [1, 1, 1, 0.71564364], 'glow_after_opacity_rgba_float': [1, 1, 1, 0.71564364], 'composed_rgba_float': None, 'pre_writeback_rgba_float': None, 'final_writeback_or_png_rgba': [123, 123, 123, 255], 'final_png_rgba_float': [0.482352941176, 0.482352941176, 0.482352941176, 1]}]}}`

## Residual Hotspot Targets

- primary_vertical_case: `{'case_id': 'kk_vertical_len50_brightness1_strength100', 'xy': [934, 118], 'windows_rgba': [131, 131, 131, 255], 'mac_bt709_candidate_rgba': [145, 145, 145, 255], 'delta': [14, 14, 14, 0]}`
- optional_rotation13_case: `{'case_id': 'kk_diagonal_len50_rotation13', 'xy': [1098, 202], 'windows_rgba': [112, 112, 112, 255], 'mac_bt709_candidate_rgba': [46, 46, 46, 255], 'delta': [-66, -66, -66, 0]}`
- 2026-06-30 hotspot inversion from the Mac witness makes the remaining Windows
  ask even narrower:
  - hotspot `(934,118)`: with source `[30,30,30]`, Windows `[131,131,131]`
    implies effective screen alpha `0.44888888...`
  - current Mac plug-in at the same hotspot uses
    `glow_alpha_after_opacity=0.507505655` and produces `out_u8=[144,144,144]`
  - the gap is therefore about `-0.0586` in effective alpha relative to the
    current Mac direct-use compose path
- 2026-07-01 hotspot-local compose diagnostic narrows it one step further:
  - using the already-grounded grayscale controls `(960,540)` and `(1010,540)`,
    the average control attenuation ratio still only projects the hotspot to
    byte `138`
  - Windows still needs byte `131`, which means there is an additional
    hotspot-only drop of `7` bytes beyond the already-grounded control behavior
  - artifact:
    `refs/conformance/olmkirakira_hotspot_local_compose_diagnostic_20260701.md`
- That means a useful Windows return only needs to answer one of three shapes:
  1. fd90/post-opacity glow alpha is already lower than Mac at the hotspot,
  2. merge-mode-1 compose attenuates the hotspot alpha below the fd90/post-opacity value,
  3. compose float matches but final pre-writeback/quantization still lowers the byte.

## Actionable Return Criteria

- It captures the internal merge-mode-1 compose-site floats or equivalent pre-writeback RGBA float at a residual hotspot.
- It captures the source RGBA float, glow RGBA float, composed RGBA float, and final u8/writeback value at the same coordinate.
- It distinguishes 'compose math already matches, only final quantization differs' from 'compose-site float is already different'.

## Not Actionable

- It only returns final PNG-facing RGBA bytes that are downstream of the unresolved compose/writeback split.
- It reopens seed luma, first-pass boxFilter, ray-helper choreography, or global compose gain without contradicting the existing grounded evidence.
- It lacks a residual hotspot coordinate and only samples already-near-matching center/up/right witnesses.

## Recommended Next Windows Probe

- At one BT.709 residual hotspot from the 9 Software cases, capture source RGBA float, glow RGBA float after fd90/opacities, merge-mode-1 composed RGBA float, pre-writeback RGBA float, and final written u8/PNG byte.
- If the compose-site float is unavailable, capture the last float before quantization/export plus the exact quantization helper or clamp path.
- Prefer a residual hotspot over center/up/right because those witnesses already ground fd90 aggregation but do not isolate the failing branch.
- Prefer hotspot `(934,118)` specifically and record the exact effective alpha
  path there. Current Mac evidence already says:
  - source gray = `30/255`
  - Mac direct-use glow alpha = `0.507505655`
  - Mac compose boundary byte = `144`
  - Windows final byte = `131`
  So a Windows answer that only repeats center/up/right or only returns final
  PNG bytes is no longer enough.
