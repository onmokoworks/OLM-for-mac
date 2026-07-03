# OLMDistanceGradation case_0023 Source-Candidates Audit

- Case: `olmdistancegradation_extended__case_0023`
- Source: `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- Residual px: `73`
- Edge bucket px: `65`
- Threshold bucket px: `8`

## Family Status

- Threshold family: `threshold-family-reference-generation-split-candidate`
  - The packaged expected PNG cannot be treated as authoritative for the case_0023 threshold triplet. The live Mac AE output at (415,393) matches the latest Windows runtime-traced final stored value, while the packaged expected PNG still shows the older blue endpoint there.
  - Next action: Keep the threshold-family triplet out of implementation tuning. Regenerate or recapture a current Windows Software reference for case_0023, or explicitly split the packaged expected lane from the current-runtime lane before touching compose/writeback.
- Edge family: `upstream-field-ownership-still-live`
  - Current Mac bg_off still differs from Windows bg_off by the same 73px cardinality. This means the residual is not just a bg_on compose issue.
  - Split: The current Mac bg_off probe agrees with Windows bg_off at (1698,7), (1700,7), (414,393), and (416,393), but still disagrees at (1699,7) and (415,393).

## Threshold Crossing Witness

| Role | XY | field_x | raw_inside |
| --- | --- | ---: | ---: |
| `below_threshold_same_row` | `(414,393)` | `0.0` | `35.0142822` |
| `first_above_threshold_same_row` | `(415,393)` | `1.0` | `36.0138855` |
| `deeper_plateau_same_row` | `(416,393)` | `1.0` | `37.0135117` |

## Edge-Family Source Candidates

| Rank | Site | Function | Line | Why live | Allowed change shape |
| --- | --- | --- | ---: | --- | --- |
| 1 | `build_distance_field_both_ownership` | `build_distance_field` | `508` | The surviving bg_off mismatch at (1699,7) keeps the case_0023 lane upstream of the final background blend. Neighboring edge witnesses already match, so the remaining live suspicion is the Both-mode ownership handoff for a narrow subset of pixels. | Both-mode ownership only; no broad field rewrite |
| 2 | `dt_to_normalized_constant_threshold` | `dt_to_normalized` | `440` | The edge-family mismatch still lives in Constant mode with Outside Threshold=0, so the binary threshold helper stays relevant if Windows current export later says the decisive edge pixel is already wrong before the Both-mode ownership merge. | helper-stage threshold ownership / plateau membership only |
| 3 | `compose_pixel_constant_endpoint` | `compose_pixel` | `558` | This remains second-order only. Reopen it only if a current Windows export or typed witness shows compose input already matches Mac while the endpoint still differs at the live edge pixel. | only with explicit Windows contradiction to current field-first reading |

## Threshold-Family Reopen Order

| Rank | Site | Function | Line | Why live | Allowed change shape |
| --- | --- | --- | ---: | --- | --- |
| 1 | `current_aex_export_provenance_gate` | `reference/export lane` | `0` | The latest live Mac AE rerun already matches the latest Windows typed triplet at (415,393), while the packaged expected PNG stays stale there. This family must stay in provenance/export classification until a same-run current Windows export lands. | no source patch until current export provenance is resolved |
| 2 | `dt_to_normalized_constant_threshold` | `dt_to_normalized` | `440` | Keep this as the first implementation reopen site only if a current Windows export or a future typed witness contradicts the current provenance split and says the threshold family is still a true output mismatch. | threshold-family reopen only after provenance contradiction |
| 3 | `compose_pixel_constant_endpoint` | `compose_pixel` | `558` | This remains second-order even for the threshold family. Reopen it only if both current export provenance and helper-stage ownership are cleared first. | only after threshold-family provenance is cleared |

## Decision Ladder

1. If the question is about the threshold-family triplet, resolve current-AEX export provenance first -> Do not patch source until the current Windows export says the family is still a true mismatch
2. If the question is about the surviving edge-family pixel and Windows says field/ownership is already wrong before compose -> Constrain changes to build_distance_field() and dt_to_normalized()
3. If Windows says compose input already matches Mac but the endpoint still differs -> Only then reopen compose_pixel()

## Forbidden Actions

- Do not promote a global Constant plateau rewrite from the rejected trunc_plateau_binary family.
- Do not retune generic 16bpc writeback from this lane.
- Do not reopen broad color-mix tuning while the field-first witness still stands.
- Do not treat the packaged expected PNG as equivalent to current Windows output for the threshold-family slice without proof.

## Active Runtime Follow-up

- Request: `olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702`
- Status: `pending`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`
- Acceptance: `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md`
- Requirement: Bind the `414/415/416,393` triplet from the output-word address or compose refcon at `FUN_181170480`; do not accept another broad callback stop with no retained XY.

## Provenance Export Follow-up

- Request: `olmdistancegradation_case0023_current_aex_recapture_20260702`
- JSON: `refs/reference_requests/olmdistancegradation_case0023_current_aex_recapture_20260702.json`
- Contract: `refs/conformance/olmdistancegradation_case0023_current_aex_export_contract_20260702.md`

