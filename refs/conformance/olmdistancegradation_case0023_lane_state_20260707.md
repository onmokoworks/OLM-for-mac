# OLMDistanceGradation case_0023 Lane State - 2026-07-07

- Case: `olmdistancegradation_extended__case_0023`
- Residual split: total `73` px = edge `65` + threshold `8`
- Safe claim: Windows packaged/current references are exact for case_0023, and the 2026-07-07 Mac AE alpha-threshold probe now matches both bg_on and bg_off Windows Software references exactly (`nonzero_px=0`, `max_diff=0`). The final/source ownership return classified the residual as low-alpha source/mask ownership plus export/path split; the Mac implementation now closes that lane with a narrow one-code-alpha source-mask threshold. Do not retune broad field, Both-merge, compose, or writeback behavior from this case without a new contradictory witness.

## Mac AE Alpha-threshold Result

- Status: `AE exact`
- Implementation: source-mask ownership treats the one-code 8bpc alpha fringe as transparent (`alpha <= 1.5/255.0` does not own the mask).
- Result: bg_on and bg_off Mac AE outputs match the corresponding Windows Software references exactly.
- Comparison: `refs/conformance/olmdistancegradation_case0023_alpha_threshold_mac_ae_result_20260707.md`
- Probe output: `refs/reports/ae_single_case_distancegradation_case0023_alpha_threshold_20260707`

| Pair | Nonzero px | Max diff |
| --- | ---: | ---: |
| `win_bg_on_vs_mac_bg_on` | `0` | `0` |
| `win_bg_off_vs_mac_bg_off` | `0` | `0` |

## Final/source Ownership Return

- Request: `olmdistancegradation_case0023_final_source_ownership_20260707`
- Status: `answered`
- Comparison: `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0023_final_source_ownership_20260707.md`
- Acceptance read: `answered_candidate`
- Pixel coverage: all requested representative/control pixels present
- Classes: `windows-source-mask`, `export-path-split`

| XY | Classification | Meaning |
| --- | --- | --- |
| `(1699,7)` | `windows-source-mask` | The low-alpha boundary differs by Windows source/mask ownership; do not reopen broad compose/helper logic from this pixel. |
| `(415,393)` | `export-path-split` | Current Windows source is opaque red, but exported PNG remains blue where prior internal final/store-side trace retained red; keep this as provenance/export evidence unless a direct exporter/writeback hook contradicts it. |

## Threshold-family

- Status: `AE exact after alpha-threshold fix`
- Summary: The packaged 2026-06-25 16bpc Windows Software reference is byte-identical to the current-AEX Windows recaptures now in the worktree. Do not use the older packaged-stale explanation for this lane.
- Next action: No further case_0023 tuning unless a broader DistanceGradation conformance case contradicts the same source-mask threshold rule.
- Authoritative request: `olmdistancegradation_case0023_current_aex_recapture_20260702`
- Request JSON: `refs/reference_requests/olmdistancegradation_case0023_current_aex_recapture_20260702.json`
- Contract: `refs/conformance/olmdistancegradation_case0023_current_aex_export_contract_20260702.md`

| XY | Live classification |
| --- | --- |
| `(414,393)` | `field_x=0.0 raw_inside=35.0142822` |
| `(415,393)` | `field_x=1.0 raw_inside=36.0138855` |
| `(416,393)` | `field_x=1.0 raw_inside=37.0135117` |

### Reference Export Audit

- Reference exact: `True`
- Safe claim: The packaged 2026-06-25 16bpc Windows Software reference is byte-identical to the 2026-07-03 and 2026-07-06 current-AEX Windows recaptures for case_0023. The old packaged-stale explanation is therefore not valid for the current files in this worktree.

| Pair | Nonzero px | Max diff | Mean diff |
| --- | ---: | ---: | ---: |
| `packaged_vs_current_win_20260703` | `0` | `0` | `0.0` |
| `packaged_vs_current_win_20260706` | `0` | `0` | `0.0` |
| `current_win_20260703_vs_20260706` | `0` | `0` | `0.0` |
| `current_win_20260706_vs_mac_live_bg_on_20260703` | `73` | `61165` | `1.0517777054398147` |
| `win_bg_off_vs_mac_bg_off_20260703` | `73` | `65535` | `1.1784258053626544` |
| `win_bg_off_vs_mac_bg_off_refresh` | `73` | `65535` | `1.1784258053626544` |

## Edge-family

- Status: `AE exact after alpha-threshold fix`
- Summary: The previous 73px bg_on/bg_off residual is closed by the narrow low-alpha source-mask threshold; current Mac AE bg_on and bg_off both compare to Windows Software with `nonzero_px=0`, `max_diff=0`.
- Next action: Preserve field-helper and compose/writeback facts; do not reopen this case unless another DistanceGradation case shows the threshold rule is too broad.
- Historical runtime request: `olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702`
- Runtime request status: `superseded_by_local_aex_cpu_simu`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`
- Acceptance: `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md`
- Live bg_off mismatches: `(1699,7), (415,393)`
- Matching bg_off neighbors: `(1698,7), (1700,7), (414,393), (416,393)`
- AEX CPU simu status: `diagnostic_binary_grounded_field_witness`
- AEX CPU simu combine: `cvAdd/saturating add modeled as min(inside+outside,1) at sampled binary outputs`

### AEX CPU Simu Reading

- Full-frame AEX CPU helper output gives both_add_saturate_field=0 at (1699,7).
- With DistanceGradation compose/invert semantics, field 0 maps to the blue Gradation endpoint for this case, matching current Mac-side field/debug behavior. The current Windows Software export is not stale, so this points at source/output ownership rather than reference drift.
- This does not by itself prove Mac AE final exact, but it strengthens the reference-path split classification for the 65px edge family.

| XY | Inside | Outside | Both-add field |
| --- | ---: | ---: | ---: |
| `(1698,7)` | `0.0` | `0.0` | `0.0` |
| `(1699,7)` | `0.0` | `0.0` | `0.0` |
| `(1700,7)` | `0.0` | `1.0` | `1.0` |
| `(1699,6)` | `0.0` | `1.0` | `1.0` |
| `(1699,8)` | `0.0` | `0.0` | `0.0` |
| `(414,393)` | `0.0` | `0.0` | `0.0` |
| `(415,393)` | `1.0` | `0.0` | `1.0` |
| `(416,393)` | `1.0` | `0.0` | `1.0` |
| `(415,392)` | `0.0` | `0.0` | `0.0` |
| `(415,394)` | `1.0` | `0.0` | `1.0` |

### Compose/Writeback Witness

- Status: `compose-writeback-triplet-binary-grounded`
- Source: `tools/emulation/test_dg_compose.py`
- Function: `DistanceGradation.aex FUN_181170480`
- Promotion rule: `trunc(half_word / 32768.0 * 65535.0)`
- Safe claim: For the case_0023 threshold triplet, executing the Windows AEX compose/writeback callback locally maps injected field_x values to the recorded runtime RGBA16 words for this witness. The 2026-07-07 reference export audit supersedes treating those recorded words as the current PNG reference at every point, so this witness is a field-to-color mapping check, not current AE exact evidence.

| XY | field_x | promoted RGBA16 | recorded RGBA16 | match |
| --- | ---: | --- | --- | ---: |
| `(414,393)` | `0.0` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `1.0` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |
| `(416,393)` | `1.0` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |

### Mac Source Model Audit

- Status: `source-model-matches-aex-helper-samples`
- Source: `scripts/materialize_distancegradation_case0023_source_model_audit.py`
- Safe claim: For the recorded case_0023 witness points, a Mac-source-shaped Constant/BOTH field model matches the Windows AEX CPU helper samples. This is not AE exact, but it makes broad field-helper retuning unsafe and keeps the live lane on reference/export/source ownership.

| XY | Mac both | AEX both | match |
| --- | ---: | ---: | ---: |
| `(1698,7)` | `0.0` | `0.0` | `True` |
| `(1699,7)` | `0.0` | `0.0` | `True` |
| `(1700,7)` | `1.0` | `1.0` | `True` |
| `(1699,6)` | `1.0` | `1.0` | `True` |
| `(1699,8)` | `0.0` | `0.0` | `True` |
| `(414,393)` | `0.0` | `0.0` | `True` |
| `(415,393)` | `1.0` | `1.0` | `True` |
| `(416,393)` | `1.0` | `1.0` | `True` |
| `(415,392)` | `0.0` | `0.0` | `True` |
| `(415,394)` | `1.0` | `1.0` | `True` |

## Forbidden

- Do not promote a global Constant plateau rewrite from the rejected trunc_plateau_binary family.
- Do not retune generic 16bpc writeback from this lane.
- Do not reopen broad color-mix tuning while the field-first witness still stands.
- Do not use the old packaged-stale explanation after the 2026-07-07 reference export audit proved packaged/current Windows exact.
- Do not retune the Both-mode saturating-add field merge while AEX CPU simu evidence says the helper already produces the live edge zero.
- Do not resend `olmdistancegradation_case0023_final_source_ownership_20260707` unless a later direct exporter/writeback hook is explicitly requested.
- Do not broaden the alpha threshold from the current one-code 8bpc fringe rule without new Windows witness evidence.

## Inputs

- threshold_json: `refs/conformance/olmdistancegradation_case0023_threshold_family_audit_20260701.json`
- source_json: `refs/conformance/olmdistancegradation_case0023_source_candidates_audit_20260701.json`
- provenance_json: `refs/conformance/olmdistancegradation_case0023_reference_provenance_20260702.json`
- bgoff_json: `refs/conformance/olmdistancegradation_case0023_bgoff_current_probe_20260702.json`
- aex_cpu_simu_json: `refs/conformance/olmdistancegradation_case0023_aex_cpu_simu_fullframe_20260707.json`
- compose_witness_json: `refs/conformance/olmdistancegradation_case0023_compose_witness_20260707.json`
- source_model_audit_json: `refs/conformance/olmdistancegradation_case0023_source_model_audit_20260707.json`
- reference_export_audit_json: `refs/conformance/olmdistancegradation_case0023_reference_export_audit_20260707.json`
