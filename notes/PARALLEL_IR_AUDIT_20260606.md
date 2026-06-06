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
3. Preparing import-time smoke hooks, AE-host package checks, and per-plugin IR notes.
4. Avoiding broad implementation changes that are not backed by binary facts
   and discriminating reference cases.

## Latest Live Pass

The 2026-06-06 live continuation pass reconfirmed the same stop lines with
fresh read-only agents:

| Plugin | Agent | Result |
| --- | --- | --- |
| OLMDirectionalBlur | `019e9a59-73e0-7ca2-8acf-15d7cb0e3bb4` / Carson | Still about 40%. `rotated-aex-full-choreo` remains red at `case_0001/case_0005 mean=4.4483/1.1703`; `rotated-aex-exact-rowdriver` remains `4.4392/1.1761`. A/B buffer choreography and scatter ownership are credible, but render-context scale and non-opaque alpha behavior remain unidentifiable from current opaque refs. |
| OLMRadialBlur | `019e9a59-7523-7822-b7e4-818bf183ec97` / Noether | Still about 55%. Zoom and Zoom Offset remain green/near-green, tiny Rotation remains green-ish, but Inner `case_0011/0012/0013` remains red at `25.2972/10.6222/21.2910`. Nonzero Size Variation refs are still required before promoting `+0x40/+0x50` plane semantics. |
| OLMKiraKira | `019e9a59-7640-7ae1-bfde-800506e00dcc` / Boole | Still about 40%. The best C++ candidate remains all-ray two-temp/no-fastpath at `case_0001/0002/0003 mean=0.8506/1.1570/1.0563`. Existing refs all use equal ray lengths and zero rotation, so single-ray refs are still required. |
| OLMSmoother / OLMSmoother2 | `019e9a59-796d-7083-8d3d-e2a5930abc22` / Newton | Standalone v1 stays low priority. `OLMSmoother2 --force-version 1` remains the preferred compatibility path for v1 refs at `mean=0.0055/0.0051/0.0200`; v2 no-key should wait for the no-key grid request. |

No implementation files were edited by these agents. The parent should not
launch more agents for the same stop-line question until at least one pending
reference request or AE-host validation result is imported.

## Latest Dispatch Follow-up

The later 2026-06-06 parent pass launched and closed fresh read-only
subagents for the highest-priority pending requests. These agents did not edit
files and reconfirmed the reference boundary:

| Plugin | Agent | Result |
| --- | --- | --- |
| OLMDirectionalBlur | `019e9ac8-c078-7e31-816b-0bfa63900ecd` / Planck | Stop line still holds. `ctx+0x11c/ctx+0x120` render scale is binary-backed, but current `--strength-scale auto = 1/frame_rate` is still PNG-fit. After `directionalblur_context_scale_20260606` import, rerun the request probe, then replace `auto` with manifest `ctx_render_scale` if present. |
| OLMSmoother2 no-key | `019e9ac8-5bbf-7620-8059-1e958565dace` / Mill | Stop line still holds. Current no-key residual is not explained by final premul; `idx0` suppression and plane-split probes worsen the result. After `smoother2_no_key_grid_20260606` import, run `python3 refs/scripts/smoke_olmsmoother2_no_key_grid_cli.py` and update `notes/OLMSmoother2_ASM_FACTS.md` with residuals grouped by Smoothness and Smooth Range before implementation. |
| OLMColorKey Replace/color-space | `019e9ac8-9396-77a3-bc6c-fc5f323ca74c` / Kierkegaard | Stop line still holds. Current refs all have `enable_replace=0`; C++ rejects Replace and Mac reads but does not write replacement colors. After `olmcolorkey_replace_colorspace_20260606` import, run the dedicated request smoke and implement only `ck_rgb_replace_red_with_blue` first. |
| OLMKiraKira | `019e9aca-3c41-77f0-86e1-562d00839611` / Hypatia | Stop line still holds. `FUN_181150790` ray helper and `FUN_18114fd90` aggregation facts remain stable, but ray order, diagonal angle table, helper scalar, crop/canvas, and any axis fast path remain unproven. After `kirakira_single_ray_20260606` import, rerun the request probe; compare vertical/horizontal first, diagonal/diagonal2 second, and Brightness 9.4 / Strength 0 last. |
| OLMRadialBlur Inner/EdgeFade | `019e9acb-34aa-7260-8030-43f053dda8c4` / Bacon | Stop line still holds. Plane ownership remains `+0x38` source RGBA, `+0x40` scatter span/gate, `+0x48` prepass alpha, and `+0x50` Size Variation factor. After `radialblur_inner_size_variation_20260606` import, rerun the request probe with `--ignore-size-variation`, then compare a small set: `+0x40` constant/validity vs sampled Size Variation, `+0x50` one vs sampled factor, and alpha-grid AEX alpha-weighted vs plain scalar sampling. |

## Verification Commands

Check request coverage:

```sh
python3 refs/scripts/check_reference_request_status.py
python3 refs/scripts/next_reference_actions.py
```

Package all pending requests for Windows rendering:

```sh
python3 refs/scripts/package_reference_requests.py --pending --output /tmp/olm_reference_requests_pending_20260606.zip
```

Package Mac plug-ins for AE-host validation:

```sh
scripts/package_mac_plugins.sh --output /tmp/olm_mac_plugins_Debug.zip
python3 scripts/verify_mac_plugin_package.py /tmp/olm_mac_plugins_Debug.zip
```

After returned refs are imported, start with the plugin-specific request smoke,
then run:

```sh
python3 refs/scripts/smoke_all_algorithm_clis.py --profile quick
```

Returned result import command:

```sh
python3 scripts/list_olm_return_candidates.py ~/Downloads /tmp
python3 scripts/intake_olm_return.py path/to/packed_reference.zip --quick --dispatch-dir /tmp/olm_reference_dispatch
python3 refs/scripts/import_and_check_win_reference.py path/to/packed_reference.zip --quick --dispatch-dir /tmp/olm_reference_dispatch
python3 refs/scripts/smoke_reference_requests_after_import.py
```

Returned AE-host validation command:

```sh
python3 scripts/intake_olm_return.py path/to/returned_ae_host.zip --require-all-pass
python3 scripts/verify_ae_host_return.py /tmp/olm_port_handoff_20260606_current.zip path/to/returned_ae_host.zip --require-all-pass
```
