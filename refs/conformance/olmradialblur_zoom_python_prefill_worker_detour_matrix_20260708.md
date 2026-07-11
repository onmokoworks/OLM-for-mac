# OLMRadialBlur Zoom Python Prefill Worker Detour Matrix

Date: 2026-07-08

## Verdict

target_sample_alpha_254_is_stable_across_single_worker_detour_matrix; target_accum_denom_cells_remain_zero_in_observed_runs

## Matrix

| Mode | prepass_calls | scatter_calls | prepass_detour_calls | scatter_detour_calls | sample_float | trunc_u8 | accum_alpha |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `both_workers_detoured` | `1` | `1` | `1` | `1` | `[0.0, 0.0, 0.0, 0.9999999924232991]` | `[0, 0, 0, 254]` | `[0.0, 0.0, 0.0, 0.0]` |
| `b150_live_scatter_detoured` | `1` | `0` | `0` | `0` | `[0.0, 0.0, 0.0, 0.9999999924232991]` | `[0, 0, 0, 254]` | `[0.0, 0.0, 0.0, 0.0]` |
| `b150_detoured_scatter_live` | `1` | `1` | `1` | `0` | `[0.0, 0.0, 0.0, 0.9999999924232991]` | `[0, 0, 0, 254]` | `[0.0, 0.0, 0.0, 0.0]` |

## Interpretation

With the validated Python prefill in place, the `(6,0)` final-plane sample keeps alpha `0.9999999924232991 -> trunc 254` when both heavy workers are no-op detoured, when `FUN_18000b150` is live and scatter is detoured, and when `FUN_18000b150` is detoured and `FUN_18000a9d0` is live. The observed four target `accum_0x842` alpha cells and `denom_0x843` cells remain zero in these runs, so this local witness continues to point at prefill/final-plane bilinear/truncate as the alpha-split explanation rather than a late byte writer.

This remains local AEX-emulation evidence, not Mac AE exact. The next implementation step should be a bounded C++ parity patch or a full-size Windows final-plane cell witness, not broad RadialBlur tuning.
