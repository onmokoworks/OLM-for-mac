# OLMDistanceGradation Depth-Gate 907 Store/Export Witness Contract - 2026-07-08

## Purpose

This is a one-pixel follow-up to
`olmdistancegradation_depthgate_quantization_witness_20260708`.

The previous return classified three of four `case_0026` representatives as
16bpc-to-export quantization. Only `(907,222)` remains unresolved:

- Windows exported RGBA8: `[255,0,0,255]`
- Mac exported RGBA8: `[255,0,1,255]`
- Mac PF_Pixel16 store words: `[32645,0,129,65535]`

Do not re-run the broad representative batch. This request exists only to bind
the Windows PF_Pixel16 store and export byte for `(907,222)` in the same run.

## Request

- Request id: `olmdistancegradation_depthgate_907_store_export_witness_20260708`
- Effect: `OLM Distance Gradation`
- Case: `olmdistancegradation_extended__case_0026`
- Bit depth: `16bpc`
- Project renderer: Windows AE Software
- Witness pixel: `(907,222)`

## Required Capture

Capture typed same-run values for `(907,222)`:

- module base and exact hook/watchpoint address
- output-world address for the target pixel
- field value consumed by `FUN_181170480`, if available at the same stop
- output RGBA float immediately before PF_Pixel16 conversion
- PF_Pixel16 words immediately after the store
- exported RGBA16 or exported display byte from the same run, if observable.
  If an image file must be generated for this witness, prefer TIFF/EXR over a
  PNG-only return.
- exact failed hook/watchpoint reason if the pixel cannot be isolated

## Acceptance

`answered`:

- The return directly proves whether Windows stores B as zero before export, or
  stores a small positive B that is rounded/truncated to exported byte zero.
- The answer includes typed PF_Pixel16 store words and either same-run export
  bytes, preferably from a TIFF/EXR-capable path when a file export is used, or
  a precise reason export could not be observed.

`answered_partial`:

- PF_Pixel16 store words are captured, but export cannot be observed.

`failed`:

- Only final PNG/display bytes are returned.
- Broad callback hit counts are returned without typed target-pixel values.
- The run repeats the previous four-pixel depthgate batch without isolating
  `(907,222)`.

## Forbidden

- Do not retune source mask, field generation, Both-combine, blur, or broad
  compose logic from this request.
- Do not include `case_0014` Layer-source work in this request.
- Do not use the AE-free CLI reimplementation as Windows truth.
