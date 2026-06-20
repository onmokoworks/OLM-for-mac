# OLM Conformance Ledger

This ledger replaces percentage-style progress tracking. The only completion
status is `AE exact`; all other states are evidence or work states.

See `notes/AE_EXACT_CONFORMANCE.md` for definitions.

## Current Feature Status

| Plug-in / feature | 8bpc Software status | 16bpc status | 32bpc status | Evidence | Next required proof |
| --- | --- | --- | --- | --- | --- |
| ColorKeep synthetic helper | guarded | untested | untested | Synthetic CLI smoke only. | Real Windows Software reference or keep as support utility. |
| OLMBlur exact slices `case_0001..0005` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0005` with `max_diff=0`; local verification report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmblur_exact_20260619/reports/ae_pixel_all_exact.json`. Non-legacy output writeback still uses a compatibility round-to-nearest-even shim while Legacy keeps `floor(x+0.5)`, so the implementation still needs binary-grounding even though the current AE cases pass. Current forecast IR: `notes/IR_OLMBlur.md`. | Binary-ground the true accumulation/writeback order behind the passing cases; then add 16/32bpc references. |
| OLMBlur residual slices `case_0006..0007` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for the formerly residual `case_0006..0007` with `max_diff=0`. 2026-06-20 runtime trace proves the remaining CLI residual is present before byte writeback: `case_0006` Windows pre-writeback red is `185.49998474121094` while Mac CLI is exactly `185.5`; `case_0007` uses the Legacy `OLMBlur+0x7FDF` writeback family. Current IR: `notes/IR_OLMBlur.md`. | Do not change the passing AE behavior from this trace alone. Only continue the CLI residual if a later proof isolates the helper accumulation/border state. |
| OLMColorKey core RGB/color-space/Replace | AE exact for core packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0008` except the Edge Blur stress case `case_0009`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmcolorkey_exact_20260619/reports/ae_pixel_all_exact.json`. Normalized CLI is exact for core `case_0001..0004` and `case_0007`. | Add 16/32bpc references for the core path after Edge Blur is isolated. |
| OLMColorKey Edge Thin erode / Edge Blur | guarded residual / partly binary-grounded | untested | untested | 2026-06-19 AE pixel return has Edge Thin erode `case_0005/0006` exact and Edge Blur `case_0008` exact; `case_0009` still fails (`max=47 mean=0.069921`). AE-free CLI residuals remain: C++ `case_0008 max=15 mean=1.1104`, `case_0009 max=255 mean=1.2503`, Edge Thin `case_0005/0006 max=255 mean=0.3031`. Mac baseline trace logs are stored under `refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac/`; Edge Thin top-edge witnesses are exactly `edge_thin_dist=17` / `edge_thin_limit=17`. | Windows runtime trace for Edge Blur `case_0009` seed/distance/weight/apply values; compare against Mac baseline before changing semantics. |
| OLMToonDilate cases `1..3` | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for `case_0001..0003` with `max_diff=0`; local report: `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmtoondilate_exact_20260619/reports/ae_pixel_all_exact.json`. AEX-style two-pass chamfer propagation plus semi-alpha RGB premultiply also makes the normalized Windows AE Software refs exact in Python and C++ CLI. Current IR: `notes/IR_OLMToonDilate.md`. | Add 16/32bpc references and keep the IR tied to the two-pass/premultiply evidence. |
| OLMDistanceGradation basic/extended/blur | AE exact for packaged 8bpc slices | untested | untested | 2026-06-19 AE pixel return is exact for all packaged basic/extended/blur cases (`12 + 16 + 1` cases, `max_diff=0`); local reports live under `refs/reports/ae_host_validation_20260619_2335/ae_pixel_olmdistancegradation_*`. CLI residuals still indicate the AE plug-in path and AE-free harness are not yet described by a fully binary-grounded shared spec. Ghidra confirms 8bpc compose is an AE iterate callback over a prebuilt field world and reads the field green byte. Current forecast IR: `notes/IR_OLMDistanceGradation.md`. | Binary-ground field prep/OpenCV args enough to make the CLI harness explain the AE exact result; then add 16/32bpc references. |
| OLMSmoother v1 via Smoother2 compatibility | AE exact for packaged 8bpc v1 slices | untested | untested | 2026-06-20 AE pixel rerun corrected the v1 comp to `960x540`; `case_0001..0003` are exact with `max_diff=0`. Local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother_v1_20260619/reports/ae_pixel_exact.json`. | Decide whether v1 remains an independent compatibility path or is formally mapped to Smoother2; add 16/32bpc refs if v1 remains supported. |
| OLMSmoother2 no-key grid | AE exact for packaged 8bpc grid | untested | untested | 2026-06-19 and 2026-06-20 AE pixel returns are exact for all 12 no-key grid cases with `max_diff=0`; latest local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_no_key_grid_20260619/reports/ae_pixel_no_key_grid_exact.json`. This supersedes the earlier AE-free near-exact residual as an AE-host conformance fact. Current IR: `notes/IR_OLMSmoother2.md`. | Optional runtime trace only for binary-grounding if it returns; do not spend the next Windows trip on no-key tuning. |
| OLMSmoother2 legacy key/gamma slices | guarded residual | untested | untested | 2026-06-20 AE pixel rerun still fails all 7 legacy cases (`max=101/254`, mean up to `0.728498`); local report: `refs/reports/ae_host_validation_20260620_1425/ae_pixel_olmsmoother2_legacy_20260619/reports/ae_pixel_legacy_exact.json`. The broader `smoke_olmsmoother2_cli.py` remains expected-red for key/gamma paths. | Prioritize runtime trace/static proof for legacy key/gamma setup and writeback; these are now the Smoother blocker, not v1 or no-key grid. |
| OLMDirectionalBlur | blocked | untested | untested | Broad PNG toggles rejected; binary facts partly documented. | New concrete asm/runtime evidence before more tuning. |
| OLMRadialBlur Zoom / tiny Rotation | guarded | untested | untested | Latest C++ guards pass: Zoom `case_0009 max=1 mean=0.0046`; tiny Rotation `case_0010 max=255 mean=0.0104` under a mean guard. These are not exact gates. Current IR: `notes/IR_OLMRadialBlur.md`. | AE exact check for Zoom slices and binary-ground the tiny Rotation high-max residual before claiming compatibility. |
| OLMRadialBlur Inner | binary-grounded / guarded | untested | untested | Runtime trace confirmed `rb_inner_only_strength_small` helper effective span resolves to `31`; C++ CLI default now mirrors the span-31 population and the span-stat guard passes. Old Inner remains expected-red: `case_0011 max=255 mean=23.0495`, `case_0012 max=255 mean=16.0039`, `case_0013 max=238 mean=18.0193`. Current IR: `notes/IR_OLMRadialBlur.md`. | Binary-ground remaining sampler/prepass/writeback residual, then Mac AE exact check. |
| OLMKiraKira strength0 / single-ray slices | binary-grounded / guarded | untested | untested | Runtime trace confirmed first `boxFilter` FilterEngine branch is OpenCV 4.5.5 AVX2 `FUN_1812e39d0`. IR now lives at `notes/IR_OLMKiraKira.md`. 2026-06-20 OpenCV 4.5.5 rerun keeps the same shape: single-ray guarded residuals `max=13/23/66`, old three-case OpenCV two-temp `case_0003 max=26 mean=1.0477`, and alias ROI byte-equivalent to ordinary two-temp. 2026-06-20 wrapper trace confirmed two `warpAffine` hits, three `boxFilter` hits, dsize `1924x1924`, length `50`, and ksize `(50,1)`, but did not isolate matrices, ROI rectangles, stage floats, aggregation, or compose values. | Need a deeper storage/sample-site trace or an AVX2 helper microprobe before changing implementation. More broad PNGs are low-value for this path. |

## Imported Runtime Proofs

- Imported `~/Downloads/olm_runtime_trace_return_windows_20260618.zip`
  with `refs/runtime_trace_packages/olm_runtime_trace_requests_20260618_075454.zip`.
- Summary files:
  - `refs/reports/runtime_trace_summary.json`
  - `refs/reports/runtime_trace_summary.md`
- Runtime facts now answered:
  - `radialblur_inner_runtime_trace_20260618`: Inner helper effective span
    resolves to `31`, matching `RCX+0x3a9ec = 31`.
  - `kirakira_opencv455_primitive_fact_20260618`: selected first
    `boxFilter` branch is `FUN_1812e39d0` / `CV_CPU_AVX2`.

- Imported `~/Downloads/olm_windows_action_bundle_20260620_overnight_blur_kirakira_return.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_1408_blur_kirakira/`.
- Summary/comparison files:
  - `refs/reports/runtime_trace_summary_olmblur_repeat_threshold_20260620.md`
  - `refs/reports/runtime_trace_comparisons/olmblur_repeat_threshold_20260620/olmblur_repeat_threshold.md`
  - `refs/reports/runtime_trace_summary_kirakira_stage_values_20260620.md`
  - `refs/reports/runtime_trace_comparisons/kirakira_stage_values_20260620/olmkirakira_stage_values.md`
- Runtime facts now answered:
  - `olmblur_repeat_threshold_runtime_trace_20260619`: `case_0006`
    residual is pre-writeback accumulation/helper drift, not only byte
    rounding; `case_0007` uses the Legacy `+0x7FDF` writeback family.
  - `kirakira_fun_181150790_stage_values_20260620`: wrapper choreography is
    confirmed, but stage values are still `trace-too-sparse`.

Re-import command:

```sh
python3 scripts/intake_olm_return.py ~/Downloads/olm_runtime_trace_return_windows_20260618.zip --runtime-package refs/runtime_trace_packages/olm_runtime_trace_requests_20260618_075454.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md
python3 refs/scripts/smoke_runtime_trace_return.py
```

## Pending Runtime Trace Requests

- OLMSmoother2 legacy key/gamma setup/writeback package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_legacy_key_gamma_20260620_154802.zip`
  (ignored local artifact, stored in the project folder for handoff). This is
  now the priority Smoother trace. It asks Windows to trace `case_0001`,
  `case_0002`, `case_0003`, and `case_0010` at top-edge witness pixels so the
  remaining `0/7` legacy failures can be classified as Color Key polarity,
  premultiply/unpremultiply, gamma setup, class-plane generation, or final
  writeback.
- OLMSmoother2 no-key grid scan/append/writeback package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_idx7_context_with_mac_baseline_20260619_041000.zip`
  (ignored local artifact, stored in the project folder for handoff). This is
  now optional/historical because the AE-host no-key grid is exact. If it
  returns, use it only to tighten binary-grounded IR and avoid PNG tuning.
- OLMBlur repeat/writeback threshold package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_with_mac_baseline_20260619_030743.zip`
  (ignored local artifact, stored in the project folder for handoff). This
  supersedes the earlier `olm_runtime_trace_olmblur_repeat_threshold_20260619_011208.zip`
  because it includes Mac baseline trace logs. It asks Windows to trace
  `case_0006` at `(498,940)` and `case_0007` at `(0,0)`, `(488,941)`,
  `(488,942)` to distinguish pre-writeback accumulation, exact tie writeback,
  and Legacy border/all_same state.
- ColorKey Edge Thin / Edge Blur package:
  `refs/runtime_trace_packages/olm_runtime_trace_colorkey_edge_erode_blur_with_mac_baseline_20260619_031350.zip`
  (ignored local artifact, stored in the project folder for handoff). This
  supersedes `olm_runtime_trace_colorkey_edge_erode_blur_20260619_025301.zip`
  because it includes Mac baseline trace logs. It traces both Edge Thin erode
  witnesses (`case_0005/0006`) and Edge Blur witnesses (`case_0008/0009`)
  around `FUN_1800094b0`, `FUN_180008c90`, `FUN_180008320`,
  `FUN_1800085b0`, and `FUN_1800049a0`.
- OLMDistanceGradation field prep / Constant mode package:
  `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip`
  (ignored local artifact, stored in the project folder for handoff). This asks
  Windows to trace `case_0020`, `case_0022`, and `case_0029` field construction,
  OpenCV `distanceTransform` / `GaussianBlur` arguments, threshold/minmax
  normalization, Constant-mode binarization, `FUN_181170870` input field bytes,
  and final compose/writeback values.

## Pending AE-Host Pixel Validation Requests

- OLMBlur exact-only request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmblur_exact_20260619_033243.zip`
  (7 normalized Software cases, exact-only thresholds).
- OLMColorKey exact-only request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmcolorkey_exact_20260619_032431.zip`
  (9 legacy ColorKey cases, exact-only thresholds). This is the ColorKey final
  gate shape; it must return `max_diff=0` for all cases to count as Mac AE
  exact evidence.
- OLMToonDilate exact-only request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmtoondilate_exact_20260619_033243.zip`
  (3 normalized Software cases, exact-only thresholds).
- OLMDistanceGradation basic exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_basic_exact_20260619_032933.zip`
  (12 normalized Software cases, exact-only thresholds).
- OLMDistanceGradation extended exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_extended_exact_20260619_032933.zip`
  (16 normalized Software cases, exact-only thresholds).
- OLMDistanceGradation blur exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmdistancegradation_blur_exact_20260619_032933.zip`
  (`case_0029`, normalized Software reference, exact-only threshold).
- OLMSmoother v1 exact request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother_v1_20260619_031933.zip`
  (3 original v1 cases, exact-only thresholds).
- OLMSmoother2 legacy key/gamma request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_legacy_20260619_031933.zip`
  (7 legacy Smoother2 cases covering key/gamma/no-key slices, exact-only
  thresholds).
- OLMSmoother2 no-key grid request:
  `refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_no_key_grid_20260619_031933.zip`
  (12 no-key grid cases, exact-only thresholds).

These are validation packages, not implementation proof by themselves. A pass
means the returned Mac AE render PNGs match the packaged Windows Software
reference PNGs with `max_diff=0`.

## Imported AE-Host Exact Proofs

- Imported `~/Downloads/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260620_1425.zip`.
- Stored copy:
  `handoffs/windows_returns/20260620_1425_smoother_priority/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260620_1425.zip`.
- Local verification directory:
  `refs/reports/ae_host_validation_20260620_1425/`.
- Exact-only result: `62/70` cases exact.
- New result relative to the previous return:
  - `OLMSmoother v1`: corrected `960x540` rerun is `3/3` exact.
- Still failing:
  - `OLMColorKey`: Edge Blur `case_0009` remains `max=47 mean=0.069921`.
  - `OLMSmoother2` legacy key/gamma slices remain `0/7` exact, with max diff
    up to `254`.
- No runtime trace result was included in this return; the runtime trace zips in
  the bundle are request packages only.

- Imported `~/Downloads/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260619_2335.zip`.
- Stored copy:
  `handoffs/windows_returns/20260619_2335/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority_progress_20260619_2335.zip`.
- Local verification directory:
  `refs/reports/ae_host_validation_20260619_2335/`.
- Exact-only result: `59/70` cases exact.
- AE exact in this return:
  - `OLMBlur`: `7/7`.
  - `OLMToonDilate`: `3/3`.
  - `OLMDistanceGradation`: basic `12/12`, extended `16/16`, blur `1/1`.
  - `OLMSmoother2` no-key grid: `12/12`.
  - `OLMColorKey`: `8/9`; `case_0009` remains a real Edge Blur residual.
- Not meaningful as algorithm failure:
  - `OLMSmoother v1`: `3/3` shape mismatches because returned candidates are
    `1920x1080` while the references are `960x540`.
- Still failing:
  - `OLMSmoother2` legacy key/gamma slices: `0/7` exact, with max diff up to
    `254`.

- Imported `~/Downloads/olm_port_handoff_ae_host_validation_20260618_172339_1_windows_result.zip`.
- Stored copy:
  `handoffs/ae_host_validation_returns/ae_host_validation_return_20260618_232926_windows.zip`.
- Summary files:
  - `refs/reports/ae_host_validation_20260618_232926/exact_return/AE_HOST_EXACT_SUMMARY.md`
  - `refs/reports/ae_host_validation_20260618_232926/exact_return/reports/AE_VALIDATION_EXACT_REPORT.md`
- Render context: Windows AE Software, `project_gpu_accel_type.current_name=SOFTWARE`, raw `1816`.
- Exact-only result: `33/48` cases exact. This is evidence, not overall
  completion, and does not replace final Mac AE exact validation.
- Failure classification:
  `refs/reports/ae_host_validation_20260618_232926/ae_host_exact_failure_classification_20260619_003051.md`.
  The main split is:
  `OLMColorKey case_0009` is a real Edge residual, `OLMDistanceGradation`
  extended/basic normalized CLI residuals still need binary-grounding, while
  `OLMBlur case_0001..0004` and `OLMToonDilate case_0001..0003` are likely
  stale packaged-reference or host-package drift because normalized returned
  Software refs are already CLI exact for those slices.
- Normalized-reference CLI triage:
  - `refs/reports/ae_host_validation_20260618_232926/normalized_refs/`
  - `refs/reports/ae_host_validation_20260618_232926/cli_checks/`
  - `OLMBlur case_0001..0005` are exact against returned Software PNGs after
    the current non-Legacy writeback shim, so the old AE-host mismatch for
    `case_0001..0004` is stale-reference drift. This is still not the final
    binary-grounded explanation because the AEX writeback constant is `0.5`.
  - `OLMToonDilate` is exact in the normalized Software CLI checks after the
    two-pass propagation/premultiply fix.
  - `OLMColorKey` Edge paths and `OLMDistanceGradation` still have
    implementation/spec residuals after normalization.
  - `OLMDistanceGradation` Blur Mode was probed under
    `refs/reports/ae_host_validation_20260618_232926/distancegradation_blur_probe/`;
    no production change was justified.

## AE Exact Proofs Still Needed

- Return AE-host pixel renders for the packaged request zips under
  `AE_PIXEL_VALIDATION/`.
- Current normalized AE-host handoff package:
  `handoffs/ae_host_validation/olm_port_handoff_ae_host_validation_normalized_20260619_003640.zip`.
  This package uses `pixel_reference_profile=normalized-20260618` so the
  OLMBlur/OLMToonDilate stale-reference drift from the first AE-host return is
  not reintroduced.
- Treat these as AE wiring and exactness checks, not as automatic completion of
  guarded slices.
- Add 16bpc and 32bpc Windows Software references after the 8bpc IR is stable.
