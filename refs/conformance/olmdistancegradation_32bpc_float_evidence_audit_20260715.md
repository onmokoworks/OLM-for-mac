# OLMDistanceGradation 32bpc FLOAT Evidence Audit

Status: Windows reference evidence is complete for the selected subset; Mac exact validation is pending and fail-closed.

## Windows evidence
- Source: `refs/win_references/20260710_190500__ae26_3_32bpc_recap/OLMbit-depthconformancebatch/reference_manifest.json`
- Provenance: Windows AE 26.3x87, 32bpc, `SOFTWARE`, float-preserving EXR.
- Strongest valid candidate subset: 29 cases (olmdistancegradation_basic: 12, olmdistancegradation_blur: 1, olmdistancegradation_extended: 16).
- Every selected case has a SHA-256-bound before-effects EXR, effect EXR, and 12 DistanceGradation parameter values.

## Mac status
- Eligible exact Mac cases: 0.
- Existing Mac evidence is 16bpc/diagnostic or field-boundary evidence. It does not provide a same-run 32bpc raw-float output for any selected EXR pair.
- Audited Mac artifacts: `refs/conformance/olmdistancegradation_fieldgen_bitdepth_boundary_20260715.json`, `refs/conformance/olmdistancegradation_16bpc_livefield_source_actual_aex_20260713.json`, and `refs/conformance/olmdistancegradation_true16_residual_family_audit_20260709.json`.
- The missing binding is listed in the JSON and enforced by the Mac request contract.

## Contract
- Request: `refs/mac_validation_requests/olmdistancegradation_32bpc_mac_validation_20260715.json`.
- A Mac result is accepted only when input identity, exact parameters, AE/project/renderer settings, plugin SHA-256, output module, and raw float output are all present and bound to the case ID.
- No PNG-only result, 16bpc result, inferred parameter match, retune, or AE-exact claim is permitted.

## Case IDs
- olmdistancegradation_basic__case_0001, olmdistancegradation_basic__case_0002, olmdistancegradation_basic__case_0003, olmdistancegradation_basic__case_0004, olmdistancegradation_basic__case_0005, olmdistancegradation_basic__case_0006, olmdistancegradation_basic__case_0007, olmdistancegradation_basic__case_0009, olmdistancegradation_basic__case_0015, olmdistancegradation_basic__case_0017, olmdistancegradation_basic__case_0018, olmdistancegradation_basic__case_0019, olmdistancegradation_extended__case_0008, olmdistancegradation_extended__case_0010, olmdistancegradation_extended__case_0011, olmdistancegradation_extended__case_0012, olmdistancegradation_extended__case_0013, olmdistancegradation_extended__case_0014, olmdistancegradation_extended__case_0016, olmdistancegradation_extended__case_0020, olmdistancegradation_extended__case_0021, olmdistancegradation_extended__case_0022, olmdistancegradation_extended__case_0023, olmdistancegradation_extended__case_0024, olmdistancegradation_extended__case_0025, olmdistancegradation_extended__case_0026, olmdistancegradation_extended__case_0027, olmdistancegradation_extended__case_0028, olmdistancegradation_blur__case_0029
