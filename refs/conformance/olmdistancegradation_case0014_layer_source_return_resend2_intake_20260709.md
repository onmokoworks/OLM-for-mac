# OLMDistanceGradation Case0014 Layer-Source Return Resend2 Intake

Date: 2026-07-09

Return archive:

- `refs/returns/windows/20260709_distancegradation_case0014_layer_source_failed/20260709_return__olm_runtime_trace_distancegradation_case0014_layer_source_witness_20260708_windows.zip`

Verification command:

- `python3 scripts/verify_runtime_trace_return.py /Volumes/onmk/olm_pr/new/20260709_return__olm_runtime_trace_distancegradation_case0014_layer_source_witness_20260708_windows.zip --package refs/runtime_trace_packages/olm_runtime_trace_distancegradation_case0014_layer_source_witness_20260708.zip --summary-json refs/reports/runtime_trace_summary.json --summary-md refs/reports/runtime_trace_summary.md`

## Classification

`failed`.

This is not an implementation proof and not an `answered_partial` result. The
resend correctly rejects the previous package-local PNG/residual-only shape, but
it still contains no fresh Windows live callback witness and no exact fresh
hook/watchpoint failure artifact.

## Missing Evidence

For `olmdistancegradation_extended__case_0014`, the required witnesses remain
missing for both `(1652,2)` and `(461,6)`:

- consumed source-layer RGBA16
- source RGB before/after unpremultiply
- ownership alpha/mask
- field channels / final `X`, `d_alpha`, `out_a`
- pre-store RGBA float before `CVTTSS2SI`
- final stored RGBA16
- exact fresh hook/watchpoint failure reason from a Windows run

## Decision

Do not change `mac/OLMDistanceGradation` from this return.

Do not resend the same package unchanged. The next useful action for this lane
would need a different Windows debug tactic that first proves a live callback
stop or returns a concrete hook/watchpoint failure condition.
