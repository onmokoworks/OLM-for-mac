# OLMKiraKira Hotspot Transform Provenance

- Case: `kk_vertical_len50_brightness1_strength100`
- Hotspot: `(934,118)`
- Status: `no-host-transform-proven`

## FACT

- Existing Windows trace compose: `0.565446166176` -> `[144, 144, 144, 255]`.
- Existing Mac compose witness: source alpha `1.0`, glow alpha `0.507505655`, output `[144,144,144,255]`.
- Archived candidate PNG: `[145, 145, 145, 255]`; canonical Windows PNG: `[131, 131, 131, 255]`.
- Returned Windows manifest context: AE `26.2x49`, render set `software`, comp `1920x1080`.
- Premultiply/unpremultiply at source alpha `1.0` is identity.
- Standard sRGB-domain screen output is `144`; linear-light blend then sRGB encoding is `190`.
- The canonical 131 implies screen glow alpha `0.448888888779`, versus traced `0.507505655000`.

## INFERENCE

- Premultiply/unpremultiply does not explain `144 -> 131` at this opaque witness.
- Standard color-management linearization does not explain it: the tested result is 190, not 131.
- Placement remains possible because the canonical image has a 131 plateau at the requested coordinate, but the local PNGs cannot establish which source pixel/stage was sampled.
- No host transform is directly proven. The evidence stays in reference/export provenance, witness placement, or an unobserved host/endgame path.

## Scope

- This report uses only existing returned trace/manifests/witnesses and PNG refs.
- It does not change Kira math, production source, ledger files, or claim AE exactness.
- Exact command:
  `python3 refs/scripts/compare_olmkirakira_hotspot_transforms.py`

## Inputs

- `refs/conformance/olmkirakira_compose_boundary_mac_witness_20260630.json`
- `refs/reports/runtime_trace_comparisons/olmkirakira_hotspot_compose_writeback_witness_20260701.json`
- `refs/reports/olmkirakira_remeasure_20260624_bt709_software/candidate/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png`
- `refs/reports/olmkirakira_remeasure_20260624_bt709_software/reference/kirakira_single_ray_20260606__software__fr24__kk_vertical_len50_brightness1_strength100.png`
- `refs/win_references/olm_reference_return_windows_20260614/OLMKiraKira/reference_manifest.json`
