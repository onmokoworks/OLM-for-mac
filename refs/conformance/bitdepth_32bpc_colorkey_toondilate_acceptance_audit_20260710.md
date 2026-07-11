# 32bpc ColorKey / ToonDilate Acceptance Audit - 2026-07-10

Status: `not-acceptable-for-AE-exact`

Scope ownership is limited to this report. No source code, request JSON, zip,
reference, or existing report was changed.

## Decision

The 2026-07-10 `OLMColorKey` (9 cases) and `OLMToonDilate` (3 cases) requests
are contractually ready for a Windows float-preserving return, but neither
lane can be accepted as `AE exact` today.

- **FACT:** The focused request package is valid and contains the two intended
  request JSON files.
- **FACT:** The request contract requires Windows AE `SOFTWARE`, `32bpc` /
  `bits_per_channel=32`, EXR first, typed float-preserving fallbacks, SHA-256,
  and header metadata. PNG-only is explicitly `probe-only`.
- **FACT:** The latest imported 32bpc returns in the repository are older
  2026-07-03 PNG-only returns. The focused ColorKey return has 18 PNGs; the
  broad/EXR-first rerun has 96 PNGs; both report
  `float_preserving_present=false` and `preferred_exr_present=false`.
- **FACT:** No returned EXR/TIFF/HDR/raw-float artifact exists for the two
  2026-07-10 requests, so there is no Windows float reference to compare and
  no Mac float candidate to compare against it.
- **INFERENCE:** Exact equality is mechanically expressible after both sides
  have verified typed float artifacts, but an AE exact acceptance decision is
  currently impossible, rather than a pass or fail.

## Audited Inputs

| Item | Evidence | Finding |
| --- | --- | --- |
| ColorKey request | `refs/reference_requests/olm_bitdepth_32bpc_colorkey_float_20260710.json` | 9 cases, `software_32bpc`, float-preserving required |
| ToonDilate request | `refs/reference_requests/olm_bitdepth_32bpc_toondilate_float_20260710.json` | 3 cases, `software_32bpc`, float-preserving required |
| Focused zip | `handoffs/windows_batch/olm_windows_reference_request_32bpc_colorkey_toondilate_float_20260710.zip` | SHA-256 `66c57c69dcbaf40c134880c80bf728120812ee3b78a8b45b74c00ca33e055f92` |
| Combined/all-plugin zip | `handoffs/windows_batch/olm_windows_reference_request_32bpc_all_plugins_exr_20260710.zip` | SHA-256 `ca18d3d79aad27c775eda2fabd8e467f63cfc57d9b472af661f77f1584789754`; it contains six specs / 98 cases but does not duplicate the focused two specs |
| Governing strategy | `notes/BIT_DEPTH_REFERENCE_STRATEGY.md:170-190` | 32bpc requires a comparator first; epsilon is not `AE exact` |
| Compare policy | `refs/conformance/bitdepth_32bpc_compare_policy_20260703.md:7-20` | Float mode, no integer truncation; exact gate is max/mean/nonzero all zero |
| Existing status | `refs/conformance/bitdepth_32bpc_probe_status_20260709.md:9-75` | Prior 32bpc returns remain PNG-only probe evidence |

## Request and Bundle Contract

**FACT:** Both JSONs declare:

- `scope.bit_depth=32bpc` and `bits_per_channel=32`.
- Required render set `software_32bpc` with
  `project_gpu_accel_type.current_name=SOFTWARE`.
- `compare_policy.mode=float-preserving-required` and PNG-only classification
  `probe-only`.
- Preferred format `exr`; fallbacks `tiff`, `tif`, `hdr`, and
  `raw-float-rgba`.
- Float-preserving output, exact format, SHA-256, and header metadata are
  required for any AE exact claim.
- Required metadata includes container, channel order/count, sample type,
  bits per channel, dimensions, color space, alpha mode, and endianness when
  applicable. All effect property names, match names, indices, values, and
  enabled/active state are also required.

**FACT:** `verify_reference_request_package.py` validates the request/package
shape and the 32bpc policy fields, including preferred EXR and PNG-only
classification. It does not validate a future returned EXR's channel types,
sample payload, NaN/Inf policy, alpha semantics, or returned-artifact hashes.

**FACT:** The focused zip contains only `README.md`, `WIN_CODEX_HANDOFF.md`,
and the two request JSONs. The all-plugin zip contains six request JSONs and
the two handoff documents. Neither is a returned reference archive.

## EXR, Float Values, and Special Values

**FACT:** `refs/scripts/verify_manifest.py` recognizes `.exr`, `.tiff`, `.tif`,
and `.hdr` as float-priority extensions and asks ImageMagick for a 32-bit
floating RGBA stream. It promotes the loaded arrays to `float64` for the
subtraction; this avoids the historical integer truncation bug.

**FACT:** The comparator does not inspect an EXR header directly. It does not
assert that the source channels are `FLOAT` rather than `HALF`, that the
channel names/order are RGBA, or that the decoder did not normalize or
quantize values before the returned stream.

**FACT:** The comparator computes `abs(reference-candidate)` and reports
`max_diff`, `mean_diff`, and nonzero pixels. There is no explicit NaN/Inf
classification. NaN can make `max_diff`/`mean_diff` NaN and fail ordinary
threshold comparisons indirectly; `+Inf - +Inf` can become NaN. This is not
a documented acceptance rule and is insufficient as a special-value audit.

**INFERENCE:** For exact acceptance, finite values should require bitwise
identical IEEE-754 float32 samples (or a documented exception profile), while
NaN should be accepted only when both sides have the same canonical NaN rule,
and Inf should require equal sign. The current comparator's zero-delta rule
does not establish those semantics by itself.

## Alpha and Premultiplication

**FACT:** The request contract requires recording `alpha_mode`, and ColorKey
also carries a `Premultiplied Color` effect parameter. The policy compares four
RGBA planes but does not define whether comparison is straight or premultiplied
alpha, how RGB is treated when alpha is zero, or whether unpremultiplication is
allowed.

**FACT:** `verify_manifest.py` uses ImageMagick `-alpha set` while extracting
  float RGBA. That is a decoder/extraction operation, not evidence that the
  original EXR was straight or premultiplied, and it does not validate the
  declared alpha mode against the manifest.

**INFERENCE:** A zero-diff RGBA result could still be semantically invalid if
the two artifacts use different alpha conventions but happen to contain
matching decoded values. Alpha mode and ColorKey premultiply behavior must be
validated before pixel comparison.

## Hashes and Metadata

**FACT:** The request JSON requires SHA-256 for every before/effect artifact,
any raw-float payload, and the returned manifest. It also requires output
header metadata including EXR channel/sample information and alpha/color
context.

**FACT:** The package verifier checks request JSON contracts, not returned
artifact hashes or media headers. `verify_manifest.py` produces pixel metrics
but does not verify SHA-256, EXR header metadata, color management, renderer
metadata, alpha mode, premultiplication, or case parameter manifests.

**INFERENCE:** `max_diff=0`, `mean_diff=0`, and `nonzero_px=0` would only prove
decoded-array equality under the selected decoder. It would not, by itself,
prove the requested AE exact evidence contract.

## Mac AE Runner Gap

**FACT:** `scripts/ae_pixel_validation_render.jsx:1-5` describes and implements
a PNG-only runner. It calls `comp.saveFrameToPng` at lines 272-289 and writes
only PNG frame names into its result summary at lines 295 and 324.

**FACT:** `scripts/verify_ae_pixel_validation_result.py:96-110` searches for
returned PNGs, and lines 178-190 copy only candidate PNGs before invoking the
manifest comparator. This path cannot consume an EXR candidate or a typed
raw-float candidate.

**FACT:** The Mac runner does set the project bits-per-channel when the
reference manifest exposes it (`ae_pixel_validation_render.jsx:300-307`), but
that setting does not make a PNG export float-preserving.

**INFERENCE:** Even after Windows returns a valid EXR, the existing Mac AE
pixel-validation path cannot produce the required comparable float artifact;
it would either reject the return or reduce the Mac side to PNG. The current
Mac runner is therefore a hard acceptance gap for 32bpc exactness.

## Minimal Fixes Required Before Return

No fixes were implemented in this audit. The smallest required follow-up is:

1. **Windows return gate:** return EXR (preferred) or a typed fallback with
   verified float sample type/bit depth, channel order/count, dimensions,
   color space, alpha mode, and endianness. Reject PNG-only as probe-only.
2. **Return integrity verifier:** verify returned manifest SHA-256 values and
   independently inspect EXR headers/channels (`R/G/B/A`, `FLOAT`/32-bit) plus
   finite/NaN/Inf counts and sign/canonicalization rules. Verify the required
   AE version, SOFTWARE renderer, 32bpc project, color settings, case IDs,
   parameters, and alpha mode.
3. **Mac float candidate path:** extend the Mac runner and its result verifier
   to export/import a typed float-preserving artifact for the same 12 cases,
   not only PNG, while preserving alpha mode and metadata.
4. **Comparator acceptance rule:** make special-value and alpha/premultiply
   rules explicit, then require the declared case set to satisfy
   `max_diff=0`, `mean_diff=0`, and `nonzero_px=0` in the verified float mode.

These are acceptance prerequisites, not implementation changes to ColorKey or
ToonDilate.

## Commands Run and Results

```sh
python3 refs/scripts/verify_reference_request_package.py \
  handoffs/windows_batch/olm_windows_reference_request_32bpc_colorkey_toondilate_float_20260710.zip
# PASS: 2 reference request(s)

python3 refs/scripts/verify_reference_request_package.py \
  handoffs/windows_batch/olm_windows_reference_request_32bpc_all_plugins_exr_20260710.zip
# PASS: 6 reference request(s)

python3 refs/scripts/smoke_verify_manifest_float_exr_delta.py
# PASS: verify_manifest preserves EXR float deltas

python3 refs/scripts/smoke_verify_manifest_exr_companion.py
# PASS: verify_manifest EXR companion smoke

find refs/win_references refs/runtime_trace_packages refs/share_staging handoffs \
  -type f \( -iname '*.exr' -o -iname '*.tif' -o -iname '*.tiff' \
  -o -iname '*.hdr' -o -iname '*.bin' \)
# PASS (audit result): no 32bpc returned float artifact found
```

The two smoke tests validate comparator behavior in synthetic fixtures; they
do not constitute ColorKey/ToonDilate AE evidence. The final acceptance state
therefore remains `not-acceptable-for-AE-exact` pending the four prerequisites
above.
