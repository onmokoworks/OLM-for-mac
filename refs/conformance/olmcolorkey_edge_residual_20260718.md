# OLMColorKey case_0005/0006 Edge Thin/Blur residual audit

Date: 2026-07-18

## Result

No production edit is justified. The apparent 9,860-pixel alpha residual in
the older `runtime_trace_comparisons/olmcolorkey_edge_trace_latest.json` is a
stale trace-pair discrepancy, not a current Edge Blur residual.

Both cases carry `Edge Blur Amount=0`, `Edge Thin Amount=-16`, and the sampled
Edge Thin distance equals its negative limit (`17`). The current AEX
`FUN_1800094b0` branch calls the output callback directly when the blur amount
is zero; it does not enter `FUN_1800085b0`, the Edge Blur apply leaf. The active
negative Edge Thin branch is inline and uses the equality-retaining comparison
already covered by the 20260718 amount matrix.

The later Mac validation record reports both `case_0005` and `case_0006` as
`max_diff=0`, `nonzero_px=0`. Therefore the old opposite-alpha trace rows do
not identify a remaining binary defect. This audit does not claim AE exactness
for all cases and does not tune PNGs.

## Verification

```text
python3 refs/scripts/smoke_olmcolorkey_edge_residual_20260718.py \
  --json refs/conformance/olmcolorkey_edge_residual_20260718.json
python3 tools/emulation/test_olmcolorkey_edge_thin_caller_amount_20260718.py
python3 tools/emulation/test_olmcolorkey_edge_thin_actual_caller_20260717.py
python3 tests/test_olmcolorkey_edge_blur_apply_differential_20260716.py
```

Machine-readable evidence: `olmcolorkey_edge_residual_20260718.json`.
The deterministic ownership/provenance test is
`refs/scripts/smoke_olmcolorkey_edge_residual_20260718.py`.
