# Parallel IR Audit 2026-06-06

This note consolidates the read-only subagent audits for the remaining hard
OLM ports. The common result is that the next useful step is returned Windows
reference data, not more PNG-only fitting.

## Summary

| Plugin | Audit result | Stop line | First action after refs return |
| --- | --- | --- | --- |
| OLMDirectionalBlur | A/B buffer choreography, alpha-weighted rotate sampler, row prepass, scatter, and output ownership are binary-backed. Current `1/frame_rate` scale fallback is not binary-backed. | Do not tune render scale, premul, or alpha ownership from current opaque refs. | Import `directionalblur_context_scale_20260606`, then remeasure `rotated-aex-full-choreo` and `rotated-aex-exact-rowdriver` with manifest/context scale. |
| OLMRadialBlur | Rotation Inner/EdgeFade plane ownership is binary-backed: `+0x38` polar RGBA, `+0x40` span/gate, `+0x48` prepass alpha, `+0x50` size factor. | Do not promote Inner/EdgeFade or Size Variation behavior from Size Variation 0 refs. | Import `radialblur_inner_size_variation_20260606`, then compare a small set of `+0x40/+0x50` plane hypotheses across size and alpha-grid cases. |
| OLMKiraKira | All rays likely pass through `FUN_181150790`; boxFilter length/anchor/border and brightness/strength split are largely binary-backed. Aggregation is not the main residual. | Do not tune equal-ray, zero-rotation refs for ray order, axis fast path, helper scalar, crop, or diagonal mapping. | Import `kirakira_single_ray_20260606`, then isolate vertical/horizontal fast path, diagonal angle table, and helper scalar. |
| OLMSmoother2 | Classifier, key path, gamma, premul writeback, and v1/v2 switching are binary-backed. v2 `--force-version 1` is the best current v1 compatibility path. | Do not tune no-key residual after the negative idx0 and plane-split probes. | Import `smoother2_no_key_grid_20260606`, then run the dedicated no-key grid smoke to classify Smoothness/Range/writeback dependence. |
| OLMColorKey | Replace and color-space branches are visible in decomp; current C++/Rust/Python reject Replace and only cover RGB/Lab76 subsets. | Do not promote Replace or non-black HSV/Lab94/YUV/YCrCb behavior from existing refs. | Import `olmcolorkey_replace_colorspace_20260606`, audit manifest coverage, then implement the smallest RGB Replace/no-edge slice first. |

## Current Decision

The hard-plugin implementation path is intentionally paused at the reference
boundary:

- `directionalblur_context_scale_20260606`
- `kirakira_single_ray_20260606`
- `olmcolorkey_replace_colorspace_20260606`
- `radialblur_inner_20260605`
- `radialblur_inner_size_variation_20260606`
- `smoother2_no_key_grid_20260606`

Until these are imported, parent work should focus on:

1. Packaging pending reference requests for the Windows machine.
2. Keeping existing green smokes passing.
3. Preparing import-time smoke hooks and per-plugin IR notes.
4. Avoiding broad implementation changes that are not backed by binary facts
   and discriminating reference cases.

## Verification Commands

Check request coverage:

```sh
python3 refs/scripts/check_reference_request_status.py
```

Package all pending requests for Windows rendering:

```sh
python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending.zip
```

After returned refs are imported, start with the plugin-specific request smoke,
then run:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
```

Returned result import command:

```sh
python3 refs/scripts/import_win_reference.py path/to/packed_reference.zip --allow-missing-optional-render-sets
python3 refs/scripts/smoke_reference_requests_after_import.py
```
