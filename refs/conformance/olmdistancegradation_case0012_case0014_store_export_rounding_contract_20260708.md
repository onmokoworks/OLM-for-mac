# OLMDistanceGradation case0012/case0014 Store/Export Rounding Contract

## Purpose

Classify the remaining 16bpc Layer/no-bg residual after the 2026-07-08
dominant-channel Both mask fix.

Mac AE currently measures:

| Case | Current Mac max true16 | Representative residual |
| --- | ---: | --- |
| `olmdistancegradation_extended__case_0012` | `2` | mostly `[-2,-2,-2,0]` |
| `olmdistancegradation_extended__case_0014` | `4` | mostly `[-2,-2,-2,0]`, with a small `[-4,-4,-4,0]` subset |

This is not a broad source-ownership request. The accepted Mac-side source rule
is recorded in `refs/conformance/olmdistancegradation_case0012_dominant_channel_closeout_20260708.md`.

## Required Witnesses

Capture at least one representative from each family:

| Case | Preferred XY | Local shape |
| --- | --- | --- |
| `case_0012` | `(438,0)` or `(657,0)` | current Mac candidate is RGB `-2`, alpha exact |
| `case_0014` | `(448,0)` or `(752,10)` | current Mac candidate is RGB `-4`, alpha exact |

For each witness, return all of:

- source RGBA16 from the AE input world
- normalized source RGBA consumed by the shader
- field `X` and `d_alpha`
- composed RGBA float immediately before PF_Pixel16 conversion
- PF_Pixel16 words immediately after store
- exported true16 value from the same run if observable, preferably TIFF or EXR

## Acceptance

`answered` requires a same-run chain binding pre-store float, PF16 store word,
and exported true16 value for at least one `case_0012` pixel and one
`case_0014` pixel.

`answered_partial` is acceptable only if the return contains either pre-store
float plus PF16 store, or PF16 store plus exported true16, with exact reason the
missing stage could not be observed.

`failed_partial`:

- final PNG/display values only
- broad hit counts
- package-local recomputation
- old/reference PNG restatement
- a `case_0012` answer without any `case_0014` witness

## Decision Rule

- If Windows pre-store float and PF16 store match Mac, but exported true16
  differs, classify as host/export rounding.
- If Windows pre-store float differs, return the source/field/compose values
  that explain the difference.
- Do not change Mac global `clamp16()` or PF16 writeback from this request
  unless both cases prove the same store/export rule.
