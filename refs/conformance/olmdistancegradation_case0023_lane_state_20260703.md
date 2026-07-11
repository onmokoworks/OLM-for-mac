# OLMDistanceGradation case_0023 Lane State - 2026-07-03

- Case: `olmdistancegradation_extended__case_0023`
- Residual split: total `73` px = edge `65` + threshold `8`
- Safe claim: threshold-family is provenance/export-first; edge-family is now closeout-first as a reference-path split / final output-export question, not a Mac helper tuning lane.

## Threshold-family

- Status: `threshold-family-reference-generation-split-candidate`
- Summary: The packaged expected PNG cannot be treated as authoritative for the case_0023 threshold triplet. The live Mac AE output at (415,393) matches the latest Windows runtime-traced final stored value, while the packaged expected PNG still shows the older blue endpoint there.
- Next action: Keep the threshold-family triplet out of implementation tuning. Regenerate or recapture a current Windows Software reference for case_0023, or explicitly split the packaged expected lane from the current-runtime lane before touching compose/writeback.
- Authoritative request: `olmdistancegradation_case0023_current_aex_recapture_20260702`
- Request JSON: `refs/reference_requests/olmdistancegradation_case0023_current_aex_recapture_20260702.json`
- Contract: `refs/conformance/olmdistancegradation_case0023_current_aex_export_contract_20260702.md`

| XY | Live classification |
| --- | --- |
| `(414,393)` | `field_x=0.0 raw_inside=35.0142822` |
| `(415,393)` | `field_x=1.0 raw_inside=36.0138855` |
| `(416,393)` | `field_x=1.0 raw_inside=37.0135117` |

## Edge-family

- Status: `reference-path-split-or-upstream-field-ownership`
- Summary: Current Mac bg_off still differs from Windows bg_off by the same 73px cardinality, so the residual is not just a bg_on compose issue. `refs/conformance/olmdistancegradation_case0023_65px_reference_path_split_20260706.md` already argued that the 65px family may be structurally unreachable through the recorded CPU pipeline, and the 2026-07-07 AEX CPU simu now adds binary-grounded helper evidence that Both add-saturate field is `0.0` at `(1699,7)`. That matches the current Mac-side field/debug reading rather than the stale/reference red endpoint, so this lane should be treated as reference-path split / final output-export closeout, not as pure Mac helper drift.
- Next action: Keep the edge-family out of Mac helper tuning. Close it with float-preserving Software/EXR recapture or typed final output/export evidence that contradicts or confirms the CPU-helper witness; do not reopen threshold-family tuning from packaged PNG drift.
- Binary-grounded helper evidence: `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`
- Closeout path: current Windows Software/EXR recapture or typed final output/export witness
- Live bg_off mismatches: `(1699,7), (415,393)`
- Matching bg_off neighbors: `(1698,7), (1700,7), (414,393), (416,393)`

## Forbidden

- Do not promote a global Constant plateau rewrite from the rejected trunc_plateau_binary family.
- Do not retune generic 16bpc writeback from this lane.
- Do not reopen broad color-mix tuning while the field-first witness still stands.
- Do not treat the packaged expected PNG as equivalent to current Windows output for the threshold-family slice without proof.
- Do not retune the Both-mode saturating-add field merge while the AEX CPU simu already produces the live edge zero.

## Inputs

- threshold_json: `refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json`
- source_json: `refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.json`
- provenance_json: `refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.json`
- bgoff_json: `refs/conformance/olmdistancegradation_case0023_bgoff_current_probe_20260702.json`
- aex_cpu_simu_json: `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`
