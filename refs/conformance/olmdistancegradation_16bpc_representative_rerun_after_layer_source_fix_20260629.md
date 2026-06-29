# OLMDistanceGradation 16bpc representative rerun after Layer/no-bg source fix

- Date: `2026-06-29`
- Request dir:
  `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Installed plug-in package:
  `/tmp/olm_mac_plugins_Debug_clean_20260629.zip`
- Fix under test:
  narrow `render_mode=Layer && use_bg=0 && src_a>0` source-ownership patch in
  `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`

## Why this rerun exists

The full AE batch renderer was unreliable on this host state, so the post-fix
behavior was rechecked through `scripts/run_ae_single_case.py` on representative
extended 16bpc cases.

## Representative results

These spot numbers came from quick local PNG-space comparisons and are useful as
visual witnesses only. They should not be treated as authoritative 16bpc
conformance metrics; see
`refs/conformance/olmdistancegradation_16bpc_batch_wrapper_rerun_20260629.md`
for the verifier-backed batch result.

| Case | Status | Current result |
| --- | --- | --- |
| `case_0012` | improved, not exact | `max=65`, `mean=1.3002979118441358`, `nonzero_px=279551`; prior factor-of-two RGB miss at witness points is reduced to `-1/-2` RGB. |
| `case_0016` | improved, not exact | `max=38`, `mean=0.10384198977623457`, `nonzero_px=13353`; representative first delta is `[-20,-20,-20,0]` at `(15,0)`. |
| `case_0020` | nearly exact | `max=238`, `mean=5.6061921296296296e-05`, `nonzero_px=1`; remaining residual is a single endpoint-selection pixel. |
| `case_0022` | boundary-localized, not exact | `max=238`, `mean=0.010763888888888889`, `nonzero_px=192`; remaining diffs stay in the previously classified Constant/boundary family. |

## Outputs

- Probe root:
  `refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/`
- Successful subruns:
  - `olmdistancegradation_extended__case_0012/`
  - `olmdistancegradation_extended__case_0016_rerun/`
  - `olmdistancegradation_extended__case_0020/`
  - `olmdistancegradation_extended__case_0022/`

## Takeaway

The new Layer/no-bg ownership patch is live in Mac AE and moves the intended
family in the right direction without regressing the already-narrow Constant
family. Remaining 16bpc work is still split between:

1. Layer/no-bg residual quantization / ownership cleanup (`case_0012`, `case_0016`)
2. Constant boundary ownership at the 1px / 192px level (`case_0020`, `case_0022`)
