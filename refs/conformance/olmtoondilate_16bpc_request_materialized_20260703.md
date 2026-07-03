# OLMToonDilate 16bpc Request Materialized - 2026-07-03

Status: `windows-reference-request-ready`

While the Windows host/addProperty diagnostics are in flight, the next
bit-depth expansion request for `OLMToonDilate` has been materialized locally.

## Artifacts

- Request JSON:
  [olm_bitdepth_16bpc_toondilate_exact_20260703.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_16bpc_toondilate_exact_20260703.json)
- Preview:
  [bit_depth_16bpc_toondilate_probe_plan_20260703/README.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/bit_depth_16bpc_toondilate_probe_plan_20260703/README.md)
- Packaged handoff zip:
  [olm_reference_request_16bpc_toondilate_exact_20260703.zip](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/runtime_trace_packages/olm_reference_request_16bpc_toondilate_exact_20260703.zip)

## Scope

- plug-in: `OLMToonDilate`
- renderer: Windows AE `SOFTWARE`
- bit depth: `16bpc`
- cases: `case_0001..case_0003`

## Reason

`OLMToonDilate` is already `AE exact` on the normalized 8bpc slice, but unlike
`OLMColorKey` it still has no first-pass 16bpc proof in-tree.

The bit-depth tooling already supported a focused `OLMToonDilate` scope, so the
highest-leverage local move was to materialize the request artifact instead of
doing more source-side speculation.

## Validation

The packaged handoff zip was checked with:

`python3 refs/scripts/verify_reference_request_package.py 'refs/runtime_trace_packages/olm_reference_request_16bpc_toondilate_exact_20260703.zip'`

and validated as a one-request package containing:

- `olm_bitdepth_16bpc_toondilate_exact_20260703`

## Next use

This zip can be published to the Windows handoff share and executed
independently of the current host-diagnostics lane.
