# OLMKiraKira Pending Compose Proof

- Historical status: `historical-superseded-by-hotspot-provenance-lane`
- Superseded by: `/Users/onmk/Documents/Projects/Personal/OLM as/refs/conformance/olmkirakira_hotspot_export_contract_audit_20260701.md`
- Why superseded: The answered 2026-07-01 hotspot witness already matches the current Mac compose-boundary values through pre-writeback and sampled RGBA8. The remaining lane is no longer live compose/quantization isolation; it is same-run export provenance, witness-placement validation, or endgame-control coverage.

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
