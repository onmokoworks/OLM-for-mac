# OLMDistanceGradation Depthgate 907 Store/Export Return Intake

Date: 2026-07-08 19:31 JST

Return zip:

- `/Volumes/onmk/olm_pr/new/20260708_return__olm_runtime_trace_olmdistancegradation_depthgate_907_store_export_witness_20260708_windows.zip`

Request:

- `olmdistancegradation_depthgate_907_store_export_witness_20260708`
- Contract: `refs/conformance/olmdistancegradation_depthgate_907_store_export_witness_contract_20260708.md`

Status:

- `answered_partial`

Accepted facts:

- The unresolved depthgate near-miss family is still narrowed to `case_0026`
  pixel `(907,222)`.
- The return preserves the previously carried values:
  - source input seen by effect: `RGBA16 = (0,65535,10794,65535)`
  - source input byte view: `RGBA8 = (0,255,42,255)`
  - field value consumed by `FUN_181170480`: `0.121742934`
  - pre-PF16-conversion float: `(0.996250153, 0.0, 0.00393153122, 1.0)`
  - carried PF_Pixel16 words: `(32645, 0, 129, 65535)`
  - carried exported byte: `RGBA8 = (255,0,0,255)`

What was not proven:

- No fresh same-run Windows debugger/watchpoint stop was captured.
- The exact Windows output-world address for `(907,222)` was not bound.
- The Windows-written PF_Pixel16 words immediately after the actual store were
  not directly observed in this return.
- No same-run TIFF/EXR-capable export observation was captured.

Classification:

- Keep this family as `depthgate-907-store-export-still-open`.
- Do not tune distance field, source mask, compose, or interpolation from this
  return.
- The only still-useful proof is a same-run store/export witness that decides
  whether Windows stores blue as `0` before export, or stores a small positive
  blue value that the export path quantizes to byte `0`.

Reproduction / generated comparison:

- `python3 scripts/intake_olm_return.py '/Volumes/onmk/olm_pr/new/20260708_return__olm_runtime_trace_olmdistancegradation_depthgate_907_store_export_witness_20260708_windows.zip' --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md --runtime-comparison-dir refs/reports/runtime_trace_comparisons`
- `python3 scripts/compare_distancegradation_trace.py --runtime-summary-json refs/reports/runtime_trace_summary.json --request-id olmdistancegradation_depthgate_907_store_export_witness_20260708 --output-json refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_907_store_export_witness_20260708.json --output-md refs/reports/runtime_trace_comparisons/olmdistancegradation_depthgate_907_store_export_witness_20260708.md`
