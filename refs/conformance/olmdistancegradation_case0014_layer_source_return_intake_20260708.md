# OLMDistanceGradation Case0014 Layer-Source Return Intake - 2026-07-08

## Classification

- Request id: `olmdistancegradation_case0014_layer_source_witness_20260708`
- Return:
  `/Volumes/onmk/olm_pr/new/20260708_return__olm_runtime_trace_distancegradation_case0014_layer_source_witness_20260708_windows.zip`
- Status: `failed_partial`
- Comparator:
  `refs/reports/runtime_trace_comparisons/olmdistancegradation_case0014_layer_source_witness_20260708.md`

## What Came Back

The return did not capture a fresh live Windows callback witness for `case_0014`.
It contains package-local PNG/residual evidence for the two selected witness
pixels:

- `(1652,2)`
- `(461,6)`

Both witnesses confirm the same shape: alpha is preserved while RGB is too low
on the current Mac side. The returned residual values report:

- Windows/reference RGBA16: `[29399, 29399, 29399, 43843]`
- Mac/candidate RGBA16: `[19713, 19713, 19713, 43843]`
- Delta: `[-9686, -9686, -9686, 0]`

This is useful confirmation of the Layer-source family shape, but it is not a
binary-grounded proof of the Windows live source/compose path.

## Missing Proof

The return explicitly does not isolate:

- live Windows consumed source-layer RGBA16
- source RGB before/after unpremultiply
- field/compose inputs
- final `X`, `d_alpha`, and output alpha
- output RGBA float immediately before conversion
- final stored RGBA16 from a same-run callback stop

## Decision

Do not change the Mac implementation from this return. If this lane is retried,
the next request must stop inside the live Windows callback and bind the two
case0014 witness pixels to source/field/compose/writeback values in the same
run. A PNG/residual restatement is not sufficient.
