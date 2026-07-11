# 32bpc Full Probe Request Materialized - 2026-07-03

Status: `windows-reference-request-ready`

The consolidated `32bpc` EXR-first float-output probe request has been
materialized as a tracked repo artifact instead of living only in `/tmp` or the
share folder.

## Artifacts

- Request JSON:
  [olm_bitdepth_32bpc_full_probe_20260703.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_full_probe_20260703.json)
- Preview:
  `refs/reports/bit_depth_32bpc_full_probe_plan_20260703/README.md`
- Packaged handoff zip:
  [olm_reference_request_32bpc_full_probe_20260703.zip](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/runtime_trace_packages/olm_reference_request_32bpc_full_probe_20260703.zip)

## Scope

- renderer: Windows AE `SOFTWARE`
- bit depth: `32bpc`
- total cases: `48`
- plug-ins:
  - `OLMBlur`
  - `OLMColorKey`
  - `OLMDistanceGradation`
  - `OLMToonDilate`

This is the broad EXR-first ask for the currently exact-origin feature groups.
It is meant to get float-preserving Windows outputs in one turn so we can stop
reasoning from PNG-only 32bpc artifacts.

## Why this is still a probe

This package intentionally keeps the current correctness bar:

- prefer `EXR` as the default 32bpc return format
- accept another float-preserving format only as a fallback
- do not promote any PNG-only 32bpc return to `AE exact`

So this bundle is useful because it broadens 32bpc coverage without weakening
the rule that exactness needs float-preserving evidence.

The request JSON now carries that contract in machine-readable form too:

- `compare_policy.path = refs/conformance/bitdepth_32bpc_compare_policy_20260703.md`
- `compare_policy.mode = float-preserving-required`
- `output_requirements.preferred_formats = ["exr"]`
- `output_requirements.png_only_classification = probe-only`

## Validation

The package was built with:

`python3 refs/scripts/package_reference_requests.py --only refs/reference_requests/olm_bitdepth_32bpc_full_probe_20260703.json --output refs/runtime_trace_packages/olm_reference_request_32bpc_full_probe_20260703.zip`

and is now the tracked source for the shared Windows request:

- share payload:
  `/Volumes/onmk/olm_pr/new/olm_reference_request_32bpc_full_probe_20260703.zip`
