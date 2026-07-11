# 32bpc Completion Matrix

Audit date: 2026-07-10. This matrix is limited to reference/package state. It
does not change scripts or source and does not stage anything to NAS.

## Decision

No 32bpc slice is complete. The current authority is
`refs/conformance/bitdepth_32bpc_probe_status_20260709.md` plus
`refs/conformance/bitdepth_32bpc_compare_policy_20260703.md`.

The 2026-07-03 focused ColorKey return, broad 48-case return, and broad
EXR-first rerun all returned PNG only. The returns prove request coverage, but
they do not preserve float samples and therefore remain `probe-only`, not
`AE exact`.

## Priority Audit

| Plugin | Prepared request evidence | Returned evidence | Current state | Next package input |
| --- | --- | --- | --- | --- |
| `OLMColorKey` | `refs/reference_requests/olm_bitdepth_32bpc_colorkey_probe_20260703.json`; `refs/runtime_trace_packages/olm_reference_request_32bpc_colorkey_probe_20260703.zip`; 9 cases, `software_32bpc`, Windows AE `SOFTWARE` | `refs/win_references/olm_reference_return_windows_20260703_32bpc_colorkey_probe/OLMbit-depthconformancebatch`; 9 cases, 18 PNG assets, no EXR/TIFF/HDR/raw float | `returned` + `probe-only`; not exact | Prepare a dedicated 9-case rerun using the same input IDs/case IDs and full effect-property manifests; require EXR first, with TIFF/HDR/raw-float fallback explicitly recorded |
| `OLMToonDilate` | Present only inside the 48-case request: `refs/reference_requests/olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json`; 3 cases, `software_32bpc`, Windows AE `SOFTWARE`; no dedicated 32bpc request package is tracked | Present only inside `refs/win_references/olm_reference_return_windows_20260703_32bpc_full_probe_exr_rerun/OLMbit-depthconformancebatch`; broad return has 48 cases and PNG-only output, no float-preserving companion | `prepared` in broad batch, `returned` in broad batch, `probe-only`; not exact | Prepare a dedicated 3-case rerun from the normalized `OLMToonDilate` source manifest, preserving the existing case IDs and asking for EXR first |

Priority inputs must use the existing normalized source cases, not newly
generated inputs:

- `OLMColorKey`: `case_0001..case_0009` from
  `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMColorKey/reference_manifest.json`.
- `OLMToonDilate`: `case_0001..case_0003` from
  `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMToonDilate/reference_manifest.json`.
- Render set: `software_32bpc`, 32 bits per channel, project renderer
  `SOFTWARE`; GPU/CUDA is out of scope.
- Preserve source asset ID, source checksum, request ID, case ID, input
  `before_effects` snapshot, complete effect names/match names/property
  indices/values, enabled and active state, AE version, project color
  settings, and `project_gpu_accel_type` name plus raw value.

## State Definitions

- **Prepared**: request JSON and package contract exist and validate, but no
  usable Windows return is attached yet.
- **Returned**: a Windows package was imported and its case/manifest receipt
  is present. `Returned` says nothing about float preservation or equality.
- **Probe-only**: returned output is PNG-only, or otherwise lacks preserved
  float samples. It may prove coverage/smoke behavior but cannot support a
  32bpc completion claim.
- **AE exact**: the declared case set has a float-preserving return and a
  verified comparison with `max_diff=0`, `mean_diff=0`, and `nonzero_px=0`.
  No current 32bpc row meets this bar.

These are orthogonal labels: a lane can be both `prepared` and `probe-only`
after a PNG return, or `returned` and `probe-only`, as in the current lanes.

## Required Float-Preserving Reference

Each returned case must include one output frame in the preferred format
`EXR`. `TIFF/TIF`, `HDR`, or a raw float RGBA dump is acceptable only when the
manifest records the exact fallback format. PNG may accompany the return for
visual inspection, but cannot substitute for the float reference.

The per-case manifest must contain:

- output path, exact format, channel names/order, sample type and precision
  (32-bit float where applicable), dimensions, alpha mode, compression, color
  space/transfer metadata, chromaticities or other file color metadata, and
  frame/time identity;
- AE version, project renderer (`SOFTWARE`), raw
  `project_gpu_accel_type`, project bit depth (`32bpc` / 32), project color
  settings, request/case IDs, input asset ID and input SHA-256;
- full effect parameter manifest and enabled/active state;
- output SHA-256 for every returned float asset, plus the manifest/package
  SHA-256. Hashes identify the bytes; they do not replace pixel comparison.

For EXR, record the actual header/channel metadata and compression. For TIFF,
record bits/sample, sample format, photometric interpretation, alpha and
embedded color metadata. For HDR, record RGBE format and color/transfer
metadata. A return missing these fields is `probe-only` until its provenance is
repaired.

## Comparison Rule

Use the existing float-preserving policy in
`refs/conformance/bitdepth_32bpc_compare_policy_20260703.md`:

- choose same-stem EXR companions when present; otherwise use the explicitly
  recorded TIFF/HDR/raw-float asset;
- compare decoded samples as `float64`, without integer conversion,
  normalization, or PNG quantization;
- compare the declared case set only after dimensions, channel layout, alpha
  mode, color metadata, and renderer metadata agree;
- claim `AE exact` only for zero difference: `max_diff=0`, `mean_diff=0`, and
  `nonzero_px=0`. Any epsilon belongs to a named exception profile and is not
  `AE exact`.

## Goal Plugins

The full goal-plugin inventory is:

`OLMBlur`, `OLMColorKey`, `OLMToonDilate`, `OLMDistanceGradation`,
`OLMRadialBlur`, `OLMDirectionalBlur`, `OLMKiraKira`, `OLMSmoother` (v1), and
`OLMSmoother2` (v2/legacy).

The current 32bpc prepared broad package covers only `OLMBlur`, `OLMColorKey`,
`OLMToonDilate`, and `OLMDistanceGradation` (48 cases). The other goal plugins
have no float-preserving 32bpc completion evidence in the audited records.

## Next Package-Preparation Inputs Only

1. Dedicated `OLMColorKey` 32bpc float return: 9 normalized cases,
   `case_0001..case_0009`, same source IDs and parameter manifests, request
   output `EXR` first, fallback `TIFF/TIF` or `HDR` or raw float RGBA, and
   require the metadata/hash fields above.
2. Dedicated `OLMToonDilate` 32bpc float return: 3 normalized cases,
   `case_0001..case_0003`, same source IDs and parameter manifests, request
   output `EXR` first, fallback `TIFF/TIF` or `HDR` or raw float RGBA, and
   require the metadata/hash fields above.
3. Both packages: render set `software_32bpc`; Windows AE `SOFTWARE`; preserve
   AE version, project color settings, raw/current GPU acceleration metadata,
   input and output SHA-256 values, and the exact request/case IDs.

Do not promote the existing PNG returns, and do not prepare NAS staging from
this matrix.
