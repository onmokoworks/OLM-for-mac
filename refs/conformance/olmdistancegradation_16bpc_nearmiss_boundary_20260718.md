# OLMDistanceGradation 16bpc near-miss boundary audit

- Date: 2026-07-18
- Scope: `case_0012` and `case_0014`, Mac-only evidence audit
- Status: `classified_not_separable_locally`
- `AE exact`: **not claimed**
- Production source and ledger: **unchanged**

## FACT

- The depth-gated Mac AE batch records case_0012 as `nonzero_px=272839`, `max_diff=64`.
- It records case_0014 as `nonzero_px=377093`, `max_diff=64`.
- The returned Windows package is `failed_partial` for `16bpc` / `SOFTWARE`.
- That return contains PNG bytes only for these representatives; it does not contain a fresh same-run Windows pre-store float, PF16 store word, or true16 TIFF/EXR value for either case.
- Mac-local direct writer evidence observes `AEX uses CVTSS2SI/CVTPS2DQ under the emulated MXCSR; this is recorded as an observation, not replaced by the Mac half-up model`.
- The writer audit explicitly leaves upstream scale as `unproven`.
- The bounded active-path census is `inactive_for_fixture` with writer hits `[]`; final output was written in that synthetic fixture: `True`.
- Existing PF16 matrix/field-staging scripts compare the Windows AEX leaves with the Mac production source on bounded synthetic buffers. They are useful local contract checks, not Windows AE conformance for 0012/0014.

## INFERENCE

- Existing evidence cannot separate host conversion from the final PF16 store for the two target cases.
- A host-conversion-only explanation is unproven because the Windows pre-store value is missing.
- A final-store-only explanation is unproven because the Windows store word is missing and the writer's upstream scale/callsite is unresolved.
- The safe classification is the upstream field/pre-store/store boundary, not a PNG/export bug and not a justified global rounding fix.
- Adjacent 0010/0011 store evidence must not be promoted to 0012/0014; its sign-flipped deltas reject one global store rule but do not identify the target-family cause.

## Required Boundary Capture

1. One Windows Software AE run per representative: source PF16 words, field raw word or float, compose pre-store float, PF16 stored word, and same-run true16 TIFF/EXR word.
2. The same coordinate, parameters, and five boundaries on Mac AE.
3. Compare each boundary separately before changing production code.

## Reproduction

```sh
python3 tools/emulation/audit_olmdistancegradation_16bpc_nearmiss_boundary_20260718.py
```

The script exits successfully only when the retained evidence still supports the fail-closed classification. It does not build, install, or modify the plugin.

## Evidence

- `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`
- `refs/reports/runtime_trace_summary_distancegradation_case0012_case0014_store_export_rounding_20260708_213751.json`
- `refs/conformance/dg_pf16_writer_boundary_20260716.json`
- `refs/conformance/dg_pf16_writer_active_path_20260716.json`
- `tools/emulation/test_dg_pf16_boundary_matrix_20260717.py`
- `tools/emulation/test_dg_pf16_field_staging_differential_20260717.py`
- `tools/emulation/test_olmdistancegradation_alpha_store_residual_20260716.py`
