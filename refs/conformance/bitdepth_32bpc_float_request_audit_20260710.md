# 32bpc Float Request Audit - 2026-07-10

Status: `pass-after-handoff-generator-fix`

## Resolution

The audit finding below was fixed on 2026-07-10. The handoff generator now
derives output instructions from selected request JSONs. Float-preserving
requests explicitly require EXR first, typed TIFF/TIF/HDR/raw-float-RGBA
fallbacks, PNG as probe-only, SHA-256, and header/sample metadata. Ordinary
requests retain their PNG workflow. The focused two-request package was
regenerated and passes both the package verifier and the handoff smoke.

Scope audited:

- [olm_bitdepth_32bpc_colorkey_float_20260710.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json)
- [olm_bitdepth_32bpc_toondilate_float_20260710.json](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/olm_bitdepth_32bpc_toondilate_float_20260710.json)
- `handoffs/windows_batch/olm_windows_reference_request_32bpc_colorkey_toondilate_float_20260710.zip`

## Finding

The request JSONs and the packaged zip passed the formal 32bpc request-package verifier, and the linked source manifests/cases exist. The original concrete defect was generated Windows handoff prose that instructed PNG-only return behavior; the resolution above closes that packaging defect.

Evidence:

- The packaged-request verifier enforces the 32bpc JSON contract only:
  [verify_reference_request_package.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/verify_reference_request_package.py:70),
  [verify_reference_request_package.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/verify_reference_request_package.py:99),
  [verify_reference_request_package.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/verify_reference_request_package.py:115)
- The handoff generator still hardcodes PNG rendering/return language:
  [package_reference_requests.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/package_reference_requests.py:209),
  [package_reference_requests.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/package_reference_requests.py:215),
  [package_reference_requests.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/package_reference_requests.py:242),
  [package_reference_requests.py](/Users/onmk/Documents/Projects/Personal/OLM as/refs/scripts/package_reference_requests.py:250)
- The packaged general README is also PNG-centric:
  [README.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/README.md:14),
  [README.md](/Users/onmk/Documents/Projects/Personal/OLM%20as/refs/reference_requests/README.md:75)

Impact:

- A Windows operator can follow the packaged handoff exactly and still return a package that violates the intended 32bpc float-preserving contract.
- This specifically weakens the `EXR`-first requirement, the typed `TIFF/TIF/HDR/raw-float-rgba` fallback rules, and the required `SHA-256` plus header-metadata recording for any non-PNG-preserving 32bpc return.

## What Verified Cleanly

- `python3 refs/scripts/verify_reference_request_package.py handoffs/windows_batch/olm_windows_reference_request_32bpc_colorkey_toondilate_float_20260710.zip`
  - `[OK] ...: 2 reference request(s)`
  - request ids:
    - `olm_bitdepth_32bpc_colorkey_float_20260710`
    - `olm_bitdepth_32bpc_toondilate_float_20260710`
- Both local JSON files byte-match the copies packaged into the zip.
- Both requests require exactly one render set:
  - `id=software_32bpc`
  - `project_gpu_accel_type.current_name=SOFTWARE`
  - `bit_depth=32bpc`
  - `bits_per_channel=32`
- Both requests declare:
  - `compare_policy.mode=float-preserving-required`
  - `compare_policy.png_only_classification=probe-only`
  - `output_requirements.preferred_formats=["exr"]`
  - `acceptable_float_preserving_fallbacks=["tiff","tif","hdr","raw-float-rgba"]`
  - `artifact_integrity.sha256_required=true`
  - `artifact_integrity.header_metadata_required=true`
- Linked normalized source manifests exist, all referenced `source_case_id` values exist, and all referenced `before_effects_frame` files exist beside those manifests.
  - `OLMColorKey` manifest SHA-256:
    `cb5048ee0da37bf4e0610b0a0773fcd57616cddf9d665d7d853a1e85e25126da`
  - `OLMToonDilate` manifest SHA-256:
    `20bca8423460b7594604f491a80ddebc6324ce1099cad86adae47c2096a5b525`

## Exact Verifier Commands Run

```sh
python3 refs/scripts/verify_reference_request_package.py \
  handoffs/windows_batch/olm_windows_reference_request_32bpc_colorkey_toondilate_float_20260710.zip

python3 refs/scripts/smoke_verify_manifest_float_exr_delta.py
python3 refs/scripts/smoke_verify_manifest_exr_companion.py
```

Verifier outcomes:

- `smoke_verify_manifest_float_exr_delta.py`: `[OK] verify_manifest preserves EXR float deltas`
- `smoke_verify_manifest_exr_companion.py`: `[OK] verify_manifest EXR companion smoke`

## Audit Boundary

No JSON edits were made. No NAS content was staged. This note owns the audit only.
