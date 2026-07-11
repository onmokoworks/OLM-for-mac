# OLMBlur 32bpc Mac/Windows Float Focus

Status: `ready-for-mac-render; no-AE-exact-claim`

## Scope

`refs/reference_requests/olmblur_32bpc_mac_windows_float_focus_20260711.json`
is the focused extraction of the authoritative 48-case request
`refs/reference_requests/olm_bitdepth_32bpc_full_probe_exr_rerun_20260703.json`.
The 48-case request contains seven OLMBlur cases. This focused artifact preserves
the exact case IDs `olmblur__case_0001` through `olmblur__case_0007`, input IDs,
full effect property manifests, and `params_full` values.

## Source And Hashes

- Normalized input source directory:
  `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur`
- Normalized source manifest:
  `refs/reports/ae_host_validation_20260618_232926/normalized_refs/OLMBlur/reference_manifest.json`
- The focused JSON records the source manifest SHA-256 and each input
  `case_000N_before_effects.png` SHA-256.
- The normalized source directory contains PNG inputs and no float EXRs.
- Float EXRs do exist for all seven OLMBlur cases in the answered-partial
  Windows return at
  `refs/win_references/20260710_185500__RETURN__olm_32bpc_existing48_exr_20260710__answered_partial_portable/OLMbit-depthconformancebatch`.
  Those returned effect and before-effects artifacts are recorded as
  `output_format=exr`, `float_preserving=true`, 32-bit FLOAT RGBA, and SOFTWARE.

## Required Run Contract

Mac and Windows use `software_32bpc`, project 32bpc, and renderer `SOFTWARE`.
EXR is preferred; typed float-preserving TIFF/TIF, HDR, or raw-float RGBA are
explicit fallbacks. PNG-only output is `probe-only`. Record exact format,
header metadata, and SHA-256 values for every artifact and manifest.

The focused JSON is consumable by
`scripts/materialize_32bpc_mac_request.py` and the resulting request directory
is consumable by `scripts/run_ae_single_case.py` with
`--output-mode exr_render_queue --output-template "<verified EXR template>"`.

This is conformance readiness and float-preserving probe evidence. It does not
claim AE exactness. An AE exact claim requires the Mac and Windows float
artifacts plus the declared 32bpc comparator to verify exact float equality.
