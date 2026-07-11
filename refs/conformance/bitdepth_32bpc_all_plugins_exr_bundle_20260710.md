# All-plugin 32bpc EXR-first reference bundle

Date: 2026-07-10

Bundle:
`handoffs/windows_batch/olm_windows_reference_request_32bpc_all_plugins_exr_20260710.zip`

This separate Windows request does not replace the active runtime-trace
exchange in `/Volumes/onmk/olm_pr/new`.

The bundle contains 98 deduplicated cases in six request specs:

| Group | Cases |
| --- | ---: |
| OLMBlur, OLMColorKey, OLMToonDilate, OLMDistanceGradation existing batch | 48 |
| OLMRadialBlur random10 | 10 |
| OLMDirectionalBlur random10 | 10 |
| OLMKiraKira random10 | 10 |
| OLMSmoother2 random10 | 10 |
| OLMSmoother v1 random10 | 10 |

The dedicated ColorKey/ToonDilate specs are not duplicated because those cases
already occur in the existing 48-case batch.

Windows requirements:

- Render every case in an AE `32bpc` project with renderer `SOFTWARE`.
- Record `project_gpu_accel_type.current_name` and raw value separately;
  `ADBE Force CPU GPU` is not a renderer verdict.
- Return EXR first. If EXR is impossible, use typed float-preserving TIFF/TIF,
  HDR, or raw-float RGBA and record the exact fallback format.
- PNG may accompany the return, but PNG-only output is `probe-only`, never
  32bpc `AE exact` evidence.
- Preserve case IDs, input IDs, parameters, enabled/active state, AE version,
  color-management settings, channel metadata, alpha mode, and SHA-256 values.

The five added groups reuse existing Windows range-metadata random10 cases.
They provide broad float-path coverage; they do not imply that Mac output is
already correct. A return becomes usable 32bpc evidence only after its
float-preserving artifact and metadata pass the comparison policy.
