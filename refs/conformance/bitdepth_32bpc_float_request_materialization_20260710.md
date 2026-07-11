# 32bpc Float Request Materialization - 2026-07-10

Status: `windows-reference-request-ready`

This note materializes two focused requests from the normalized source cases and the 20260703 request schemas.

## Requests

- [olm_bitdepth_32bpc_colorkey_float_20260710.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json)
  - `OLMColorKey`, cases `case_0001..case_0009`
- [olm_bitdepth_32bpc_toondilate_float_20260710.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_toondilate_float_20260710.json)
  - `OLMToonDilate`, cases `case_0001..case_0003`

Both requests require Windows After Effects `SOFTWARE`, `32bpc`, and `bits_per_channel=32`. The normalized source parameters and case membership are copied from the existing 20260703 request shapes.

Project-local handoff package:

- `handoffs/windows_batch/olm_windows_reference_request_32bpc_colorkey_toondilate_float_20260710.zip`
- Package verification: `2` request specs, ColorKey `9` cases and ToonDilate
  `3` cases.
- This package is prepared but not staged to `/Volumes/onmk/olm_pr/new` while
  a higher-priority runtime witness is being selected.

## Return Contract

- Preferred output: typed float-preserving `EXR`.
- Typed fallbacks: `TIFF/TIF`, `HDR`, or `raw-float-rgba`, with the exact format, sample type, channel order/count, dimensions, color space, alpha mode, and endianness when applicable recorded in the manifest.
- SHA-256 is required for every before/effect artifact, raw-float payload when used, and the returned manifest.
- PNG-only output is retained as probe material and is not AE exact evidence.

The 20260703 comparison policy remains the governing comparator contract: [bitdepth_32bpc_compare_policy_20260703.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/conformance/bitdepth_32bpc_compare_policy_20260703.md).

## Validated Inputs

The requests reference these normalized manifests:

- `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey/reference_manifest.json`
- `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMToonDilate/reference_manifest.json`

The validator checked that each manifest exists, every referenced `source_case_id` exists, and every `before_effects_frame` exists beside its manifest.

Source manifest SHA-256 values:

| Manifest | SHA-256 |
| --- | --- |
| OLMColorKey | `cb5048ee0da37bf4e0610b0a0773fcd57616cddf9d665d7d853a1e85e25126da` |
| OLMToonDilate | `20bca8423460b7594604f491a80ddebc6324ce1099cad86adae47c2096a5b525` |

## Evidence Boundary

These are reference requests, not results. No AE exact claim is made here. A returned case can enter 32bpc comparison only after the Windows render set, float-preserving format, hashes, and header metadata are verified.
