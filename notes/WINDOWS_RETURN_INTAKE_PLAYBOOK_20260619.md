# Windows Return Intake Playbook 2026-06-19

This note is for returns from the current Windows helper bundles. The active
overnight target is:

`handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`

Older notes below still document the 2026-06-19 Smoother-first bundle:

`handoffs/windows_batch/olm_windows_action_bundle_20260619_041000_smoother_idx7_context_priority.zip`

The bundle is Smoother-first, but it also includes OLMBlur, OLMColorKey Edge,
OLMDistanceGradation runtime traces and exact-threshold AE pixel validation
requests.

## Bundle Audit

Verified locally on 2026-06-19:

- `python3 refs/scripts/smoke_windows_action_bundle.py` passes.
- Bundle manifest kind is `olm_windows_action_bundle`.
- Priority is `smoother-first`.
- Nested packages:
  - 4 runtime trace request zips:
    OLMSmoother2 no-key grid, OLMBlur repeat/writeback threshold,
    OLMColorKey Edge Thin/Edge Blur, OLMDistanceGradation field prep.
  - 9 AE pixel validation request zips:
    OLMSmoother v1, OLMSmoother2 legacy, OLMSmoother2 no-key grid,
    OLMBlur exact, OLMToonDilate exact, OLMColorKey exact,
    OLMDistanceGradation basic/extended/blur exact.
- Each nested zip is validated as either
  `runtime-trace-request-package` or `ae-pixel-validation-request`.

This audit only proves that the request bundle is well-formed. It does not
prove any plug-in is complete; completion still requires returned Mac AE
`max_diff=0` for the covered case group.

## 2026-06-20 Blur/KiraKira Overnight Bundle

Current send target:

`handoffs/windows_batch/olm_windows_action_bundle_20260620_overnight_blur_kirakira.zip`

This bundle is runtime-only and focused on:

- OLMBlur repeat/writeback threshold:
  `refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_20260620_overnight.zip`
- OLMKiraKira `FUN_181150790` stage values:
  `refs/runtime_trace_packages/olm_runtime_trace_kirakira_stage_values_20260620_overnight.zip`

When the KiraKira runtime trace returns, intake it with the matching package:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/olm_runtime_trace_kirakira_stage_values_20260620_overnight.zip \
  --runtime-summary-json refs/reports/runtime_trace_summary_kirakira_stage_values_20260620.json \
  --runtime-summary-md refs/reports/runtime_trace_summary_kirakira_stage_values_20260620.md \
  --runtime-comparison-dir refs/reports/runtime_trace_comparisons
```

Then compare the Windows facts against the local OpenCV baseline:

```sh
python3 scripts/compare_kirakira_stage_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary_kirakira_stage_values_20260620.json \
  --local-trace-json refs/reports/olmkirakira_trace_baseline_20260620_overnight_mac/trace.json \
  --output-json refs/reports/olmkirakira_stage_trace_comparison_20260620.json \
  --output-md refs/reports/olmkirakira_stage_trace_comparison_20260620.md
```

Interpretation:

- `ray-length-normalization`: update parameter normalization before touching
  OpenCV math.
- `warp-matrix-or-center`: update IR for center/dsize/copy rectangles before
  changing the C++/Mac path.
- `boxfilter-stage-values`: inspect box pass samples and selected branch; do
  not retune anchor/normalize/border without contradiction.
- `aggregation-or-compose`: leave ray helper alone and focus
  `FUN_18114fd90` / merge-mode-1 compose.
- `trace-too-sparse`: request missing values instead of PNG tuning.

## Priority Order

1. OLMSmoother2 runtime trace
   - Request package:
     `refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_idx7_context_with_mac_baseline_20260619_041000.zip`
   - Reason: current no-key grid is near-exact but not exact. The decisive
     question is whether Windows differs in scanner endpoint/context, appended
     samples, composite/writeback, or only final AE-host output.
   - First values to compare:
     `FUN_180010550` p1/p2/p3 plus idx=7 context, `d520/dbd0/d230/d800`
     helper returns, `FUN_1800104d0` append sequence, `FUN_18000ab00`,
     `FUN_18000b120`, and `FUN_1800036e0` final values.

2. OLMBlur runtime trace
   - Request package:
     `refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_with_mac_baseline_20260619_030743.zip`
   - Reason: `case_0006` has a single tie-like residual and `case_0007` has a
     legacy border/tie residual. Do not change `nearbyint` or legacy border
     exclusion without trace evidence.

3. OLMColorKey Edge runtime trace
   - Request package:
     `refs/runtime_trace_packages/olm_runtime_trace_colorkey_edge_erode_blur_with_mac_baseline_20260619_031350.zip`
   - Reason: Edge Thin erode is exact in AE-host return but not CLI; Edge Blur
     `case_0009` is the current final-risk ColorKey slice.

4. OLMDistanceGradation runtime trace
   - Request package:
     `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip`
   - Reason: compose math is binary-grounded, but Constant field prep,
     `distanceTransform`, `GaussianBlur`, and field-world packing are not exact
     yet.

5. AE pixel validation returns
   - These are exact-threshold Mac AE gates for selected current refs. Passing
     them is stronger than CLI exact, but still only for the covered 8bpc
     cases. 16bpc and 32bpc remain separate work.

## Runtime Trace Intake

Use the specific package when possible, not the newest package heuristic:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/olm_runtime_trace_olmsmoother2_no_key_grid_idx7_context_with_mac_baseline_20260619_041000.zip \
  --runtime-summary-json refs/reports/runtime_trace_summary_smoother2_20260619.json \
  --runtime-summary-md refs/reports/runtime_trace_summary_smoother2_20260619.md
```

Then run:

```sh
python3 refs/scripts/smoke_runtime_trace_return.py
```

For a return that may contain any of the known trace requests, run the
comparison index after writing the normalized summary:

```sh
python3 scripts/compare_runtime_trace_summary.py \
  --runtime-summary-json refs/reports/runtime_trace_summary.json \
  --output-dir refs/reports/runtime_trace_comparisons
```

Or let intake write the summary and comparison index in one step:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-summary-json refs/reports/runtime_trace_summary.json \
  --runtime-summary-md refs/reports/runtime_trace_summary.md \
  --runtime-comparison-dir refs/reports/runtime_trace_comparisons
```

This auto-runs the available routers for present request IDs:

- `scripts/compare_olmblur_trace.py`
- `scripts/compare_kirakira_stage_trace.py`
- `scripts/compare_colorkey_edge_trace.py`
- `scripts/compare_distancegradation_trace.py`

The index files are:

- `refs/reports/runtime_trace_comparisons/index.json`
- `refs/reports/runtime_trace_comparisons/index.md`

For multi-request returns, repeat intake with the matching package if the
Windows helper returns one package at a time. If Windows returns a single
combined artifact, inspect `request_id` values first and use the package that
matches the dominant request set.

## OLMBlur Runtime Comparison

For OLMBlur repeat/writeback returns, summarize with the matching package and
compare against the existing Mac baseline logs:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/olm_runtime_trace_olmblur_repeat_threshold_20260620_overnight.zip \
  --runtime-summary-json refs/reports/runtime_trace_summary_olmblur_repeat_threshold_20260620.json \
  --runtime-summary-md refs/reports/runtime_trace_summary_olmblur_repeat_threshold_20260620.md \
  --runtime-comparison-dir refs/reports/runtime_trace_comparisons

python3 scripts/compare_olmblur_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary_olmblur_repeat_threshold_20260620.json \
  --local-baseline-dir refs/reports/olmblur_trace_baseline_20260619_030633_mac \
  --output-json refs/reports/olmblur_trace_comparison_20260620.json \
  --output-md refs/reports/olmblur_trace_comparison_20260620.md
```

The comparison's `likely_next_focus` field is only a router:

- `nonlegacy-accumulation-or-writeback`: decide whether `case_0006` differs
  before or only at byte writeback.
- `legacy-border-or-all-same`: settle `case_0007` border inclusion and
  all-same helper state.
- `trace-structure-present-values-missing`: return the requested per-pixel
  values before changing code.
- `trace-too-sparse`: request missing residual-pixel values instead of PNG
  tuning.

## AE Pixel Intake

For exact-threshold AE pixel validation returns:

```sh
python3 scripts/intake_olm_return.py path/to/returned_ae_host_or_pixel.zip \
  --require-all-pixel-requests
```

If the return is specifically one request package, verify with the matching
request zip:

```sh
python3 scripts/verify_ae_pixel_validation_result.py \
  refs/ae_pixel_validation_packages/olm_ae_pixel_validation_olmsmoother2_no_key_grid_20260619_031933.zip \
  path/to/returned_ae_pixel.zip \
  --run-dir refs/reports/ae_pixel_validation_olmsmoother2_no_key_grid_20260619_return
```

## Decision Rules

- `max_diff=0` from Mac AE exact validation is the only completion evidence for
  that covered case group.
- Runtime trace equality can justify an implementation change or rule out a
  suspected bug, but it is not completion by itself.
- Guarded CLI passes are regression checks only.
- If a runtime trace contradicts current CLI behavior, update the matching IR
  first, then implement the narrowest binary-backed change.
- If a runtime trace is incomplete, request the missing values instead of
  tuning from PNG residuals.

## ColorKey Edge Runtime Comparison

For ColorKey Edge returns, summarize with the matching package and compare
against the existing Mac baseline logs:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/olm_runtime_trace_colorkey_edge_erode_blur_with_mac_baseline_20260619_031350.zip \
  --runtime-summary-json refs/reports/runtime_trace_summary_colorkey_edge_20260619.json \
  --runtime-summary-md refs/reports/runtime_trace_summary_colorkey_edge_20260619.md

python3 scripts/compare_colorkey_edge_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary_colorkey_edge_20260619.json \
  --local-baseline-dir refs/reports/olmcolorkey_edge_trace_baseline_20260619_031239_mac \
  --output-json refs/reports/olmcolorkey_edge_trace_comparison_20260619.json \
  --output-md refs/reports/olmcolorkey_edge_trace_comparison_20260619.md
```

The comparison's `likely_next_focus` field is only a router:

- `edge-thin-border-threshold`: inspect top-edge erode seed/threshold before
  touching Edge Blur.
- `edge-blur-seed-world`: update the boundary/seed-world IR first.
- `edge-blur-apply-or-compose`: focus the apply/blend formula and final RGBA.
- `trace-too-sparse`: request missing seed/distance/weight/apply values.

## DistanceGradation Runtime Comparison

For OLMDistanceGradation field-prep returns, summarize with the matching
package and classify which binary-backed rule should move next:

```sh
python3 scripts/intake_olm_return.py path/to/returned_runtime_trace.zip \
  --kind runtime-trace \
  --runtime-package refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_field_prep_opencv_args_20260619_030427.zip \
  --runtime-summary-json refs/reports/runtime_trace_summary_distancegradation_field_prep_20260619.json \
  --runtime-summary-md refs/reports/runtime_trace_summary_distancegradation_field_prep_20260619.md

python3 scripts/compare_distancegradation_trace.py \
  --runtime-summary-json refs/reports/runtime_trace_summary_distancegradation_field_prep_20260619.json \
  --output-json refs/reports/olmdistancegradation_trace_comparison_20260619.json \
  --output-md refs/reports/olmdistancegradation_trace_comparison_20260619.md
```

The comparison's `likely_next_focus` field is only a router:

- `constant-field-prep`: update field construction/packing IR before touching
  compose.
- `threshold-normalization`: settle clamp/minmax denominator before Gaussian
  or compose changes.
- `distance-transform-args`: update OpenCV/helper primitive assumptions first.
- `gaussian-blur-args`: focus `case_0029` blur radius/kernel/border.
- `compose-field-byte`: focus `FUN_181170870`
  green-byte/invert/interp/writeback.
- `trace-too-sparse`: request missing field/OpenCV/compose values instead of
  PNG tuning.

## Post-Intake Commands

After any return has been imported or verified:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile nonhard
python3 refs/scripts/generate_port_dashboard.py
python3 scripts/print_next_olm_action.py handoffs/windows_batch refs/runtime_trace_packages refs/ae_pixel_validation_packages
```

Record important facts in:

- `notes/IR_OLMSmoother2.md`
- `notes/IR_OLMBlur.md`
- `notes/IR_OLMColorKey_Edge.md`
- `notes/IR_OLMDistanceGradation.md`
- `notes/CONFORMANCE_LEDGER.md`
