# OLMDistanceGradation 0010/0011 Field/Store Witness Contract

Date: 2026-07-09

## 2026-07-09 Return Status

The Windows returns for this request are `failed_partial`.

The earlier return usefully restated the local/implied store directions, but it
did not include fresh same-run Windows runtime values. The later live CDB retry
launched AE, but did not reach the `DistanceGradation.aex` module-load stop, so
the coordinate-gated hooks never armed and all requested values remained null.
Treat these returns as evidence that the family is narrow and that the hook path
needs prewarm/module-load reliability, not as proof of the implementation rule.

Do not answer a retry with package-local recomputation, PNG residual direction,
or Windows-implied store words. The missing proof is the live Windows AEX path
for the exact target pixels in the same render.

## Purpose

This request is a narrow Windows Software runtime witness for the remaining
OLMDistanceGradation true16 `case_0010/0011` sparse R/A family.

Do not answer this with a broad PNG batch. The local Mac-side evidence already
shows:

- canonical true16 `case_0010` has `max=2`, `nonzero=351`, R/A only.
- canonical true16 `case_0011` has `max=2`, `nonzero=501`, R/A only.
- Mac Meijster EDT and the repository OpenCV-compatible EDT agree bit-for-bit at
  the target distance-field points.
- simple local field-pack/store simulations do not classify the family safely.
- the visible R/A `±2` deltas imply a one-word PF_Pixel16 alpha-store split, and
  the sign flips by point, so a global `clamp16()` rounding change is forbidden.

## Required Cases And Pixels

Trace the exact 16bpc Software request cases from
`handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625/`.

Primary pixels:

- `olmdistancegradation_extended__case_0010` at `(6,40)`.
  - Mac store is one word lower than implied Windows.
  - Mac debug: `field_x=0.9002838730812073`, `out_a=0.09971612691879272`,
    `out_a*32768=3267.498046875`, Mac `store_a=3267`, Windows-implied
    `store_a=3268`.
- `olmdistancegradation_extended__case_0010` at `(901,394)`.
  - Mac store is one word higher than implied Windows.
  - Mac debug: `field_x=0.6985930800437927`, `out_a=0.3014069199562073`,
    `out_a*32768=9876.501953125`, Mac `store_a=9877`, Windows-implied
    `store_a=9876`.

Optional control pixel:

- `olmdistancegradation_extended__case_0011` at `(915,392)`.
  - Mac store is one word higher than implied Windows.
  - Mac debug: `field_x=0.1345367729663849`, `out_a=0.8654632568359375`,
    `out_a*32768=28359.5`, Mac `store_a=28360`, Windows-implied
    `store_a=28359`.

## Values To Capture

For each target pixel, capture same-run typed values from the Windows AEX path:

- source RGBA16 consumed by the effect callback.
- inside/outside raw distance values before normalization.
- normalized field value consumed by final compose.
- field-world stored word/value if an intermediate field world exists.
- final compose `out_a` and RGBA floats immediately before PF_Pixel16
  conversion.
- final PF_Pixel16 stored RGBA words immediately after writeback.
- exported true16/TIFF/EXR sample if observable from the same render.

PNG/display bytes alone are not sufficient. Prefer TIFF or EXR for exported
samples when available.

The minimum useful retry is one primary `case_0010` pixel with fresh Windows
values at every stage above. A satisfactory retry captures both primary pixels.
Given the sign flip between `(6,40)` and `(901,394)`, the next practical retry
should capture both primary pixels in the same run if at all possible.

## Acceptance Rule

Classify the split as one of:

- Windows field/normalization differs before compose.
- Windows pre-store float matches Mac, but PF_Pixel16 conversion differs.
- Windows PF_Pixel16 store matches Mac, but AE export differs.
- The hook could not bind the final writer; return exact failed hook/watchpoint
  reason and the closest retained frame with source, field, pre-store, store, and
  export context.

One fully typed primary pixel is partial. Both primary pixels with field,
pre-store, store, and export context are satisfactory.
