# OLMDistanceGradation case0012/case0014 Store/Export Rounding Return Intake - 2026-07-08

## Verdict

`failed_partial`.

The returned zip does not satisfy
`refs/conformance/olmdistancegradation_case0012_case0014_store_export_rounding_contract_20260708.md`.
It contains package-local PNG bytes and carried notes, but no fresh same-run
Windows trace binding the requested pre-store float, PF16 store word, and
exported true16 value.

## Source

- Return zip:
  `/Volumes/onmk/olm_pr/new/20260708_return__olm_runtime_trace_olmdistancegradation_case0012_case0014_store_export_rounding_20260708_windows.zip`
- Normalized summary:
  `refs/reports/runtime_trace_summary_distancegradation_case0012_case0014_store_export_rounding_20260708_213751.json`
- Summary markdown:
  `refs/reports/runtime_trace_summary_distancegradation_case0012_case0014_store_export_rounding_20260708_213751.md`

## Directly Observed

- Package-local PNG bytes for the requested `case_0012` representatives:
  - `(438,0)` output RGBA8 = `[165,165,165,253]`
  - `(657,0)` output RGBA8 = `[234,234,234,253]`
- Package-local PNG bytes for the requested `case_0014` representatives:
  - `(448,0)` output RGBA8 = `[78,78,78,141]`
  - `(752,10)` output RGBA8 = `[78,78,78,141]`

## Missing Contract Evidence

For both `case_0012` and `case_0014`, the return is missing:

- direct Windows pre-store RGBA float;
- direct Windows PF_Pixel16 store word;
- same-run exported TIFF/EXR true16 value.

The `case_0012` carried lane summary is useful context, but it is not a fresh
Windows stop from this return. `case_0014` still has no fresh live Windows
callback/store/export witness.

## Decision

Do not change Mac `OLMDistanceGradation` from this return.

The remaining Layer/no-bg max `2/4` family stays open as a store/export
rounding proof lane. A retry must capture one representative from `case_0012`
and one representative from `case_0014` with the full same-run chain:

1. source RGBA16 from AE input world;
2. normalized source RGBA consumed by the shader;
3. field `X` and `d_alpha`;
4. composed RGBA float before PF16 conversion;
5. PF16 words immediately after store;
6. exported TIFF/EXR true16 value from the same run.

PNG/display bytes alone remain failure evidence, not implementation proof.
