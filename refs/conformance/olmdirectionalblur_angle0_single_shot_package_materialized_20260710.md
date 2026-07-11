# OLMDirectionalBlur Angle-0 Single-Shot Package Materialized - 2026-07-10

- Profile: `directionalblur-angle0-single-shot-witness`
- Contract: `refs/conformance/olmdirectionalblur_angle0_single_shot_witness_contract_20260708.md`
- Request id: `olmdirectionalblur_angle0_single_shot_witness_20260708`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_single_shot_20260710.zip`
- Materialization status: `materialized`

## Package Verification

- The ZIP is valid and contains 23 entries.
- The manifest profile is `directionalblur-angle0-single-shot-witness`.
- The manifest entrypoint is the contract above.
- The manifest contains exactly the requested single runtime action.
- The return template contains the same single request id.
- The package includes the real request set `refs/reference_requests/directionalblur_context_scale_20260606.json` and the angle-0 contract/supporting evidence.
- No Windows runtime return or typed witness values are claimed by this materialization.

## Smokes

- `python3 refs/scripts/smoke_runtime_trace_package.py` passed.
- `python3 refs/scripts/smoke_compare_directionalblur_trace.py` passed with `[OK] DirectionalBlur trace comparison smoke`.

This artifact is a project-local request package only; no files were staged to `/Volumes`, and no source or shared scripts were changed.
