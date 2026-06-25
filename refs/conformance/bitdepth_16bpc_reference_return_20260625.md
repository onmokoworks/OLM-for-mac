# 16bpc Windows Software Reference Return - 2026-06-25

- Request: `olm_bitdepth_16bpc_normalized_exact_20260625`
- Status: `reference-covered-compare-pending`
- Reference kind: `windows_ae_software`
- Render set: `software_16bpc`
- AE version: `26.2x49`
- Project renderer: `SOFTWARE`
- Imported manifest: `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json`
- Manifest SHA-256: `c4378358c8b4db2b2d5d12d0bf0b4142f141963538ca5ec4d86a49eeb8b9e71e`

## Coverage

| Feature group | Cases |
| --- | ---: |
| `OLMBlur` | 7 |
| `OLMColorKey` | 9 |
| `OLMDistanceGradation basic` | 12 |
| `OLMDistanceGradation extended` | 16 |
| `OLMDistanceGradation blur` | 1 |

Total: 45 cases.

## Verification

- `python3 refs/scripts/import_win_reference.py ... --set-id olm_bitdepth_16bpc_normalized_exact_20260625 --request refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json --replace`
- `python3 refs/scripts/verify_reference_request_result.py --allow-missing-optional-render-sets refs/reference_requests/olm_bitdepth_16bpc_normalized_exact_20260625.json refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json`
- `python3 refs/scripts/check_reference_request_status.py --requests refs/reference_requests --references refs/win_references`
- `file refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmblur__case_0001.png`

The verifier reports 45 required request cases and 45 matching rendered cases.
The sampled OLMBlur PNG is `16-bit/color RGBA`.

## Not Complete

This is not an `AE exact` result. It proves that the Windows Software 16bpc
reference set exists and is internally consistent. Completion for these
feature/bit-depth slices still requires Mac AE 16bpc output for the same cases
and a 16bpc-aware `max_diff=0` comparison.
