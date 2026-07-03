# OLMColorKey 32bpc Request Materialized - 2026-07-03

Status: `windows-reference-request-ready`

The focused 32bpc probe request for `OLMColorKey` has been materialized from
the existing bit-depth tooling.

## Artifacts

- Request JSON:
  [olm_bitdepth_32bpc_colorkey_probe_20260703.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_colorkey_probe_20260703.json)
- Preview:
  [bit_depth_32bpc_colorkey_probe_plan_20260703/README.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reports/bit_depth_32bpc_colorkey_probe_plan_20260703/README.md)
- Packaged handoff zip:
  [olm_reference_request_32bpc_colorkey_probe_20260703.zip](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/runtime_trace_packages/olm_reference_request_32bpc_colorkey_probe_20260703.zip)

## Scope

- plug-in: `OLMColorKey`
- renderer: Windows AE `SOFTWARE`
- bit depth: `32bpc`
- cases: `case_0001..case_0009`

## Why this is a probe, not completion

`OLMColorKey` already has strong 8bpc and 16bpc evidence in-tree, but 32bpc is
still unverified.

This request explicitly preserves the current policy boundary:

- prefer float-preserving output such as EXR or raw float samples
- do not treat PNG-only 32bpc returns as `AE exact`

So the request is useful because it makes the next external step concrete
without weakening the correctness bar.

## Validation

The packaged handoff zip was validated with:

`python3 refs/scripts/verify_reference_request_package.py /Users/onmk/Documents/Projects/Personal/OLM\ as/refs/runtime_trace_packages/olm_reference_request_32bpc_colorkey_probe_20260703.zip`

and confirmed as a one-request package containing:

- `olm_bitdepth_32bpc_colorkey_probe_20260703`
