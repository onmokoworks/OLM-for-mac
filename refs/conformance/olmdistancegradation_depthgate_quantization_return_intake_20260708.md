# OLMDistanceGradation Depth-Gate Quantization Return Intake 2026-07-08

## Source

- Return zip: `olm_runtime_trace_olmdistancegradation_depthgate_quantization_witness_20260708_return_windows_20260708.zip`
- Request: `olmdistancegradation_depthgate_quantization_witness_20260708`
- Intake status: `answered`
- Summary source: `refs/reports/runtime_trace_summary.json`

## Facts

The return classifies the clean `case_0026` max=1 near-miss family primarily as
16bpc-to-export quantization, not distance-field topology or broad compose math.

Representative `case_0026` pixels:

| xy | classification | Windows exported RGBA8 | PF_Pixel16 words after store |
| --- | --- | --- | --- |
| `(907,222)` | `unresolved` | `[255,0,0,255]` | `[32645,0,129,65535]` |
| `(395,477)` | `export-quantization` | `[253,0,2,255]` | `[32513,0,268,65535]` |
| `(1589,579)` | `export-quantization` | `[134,0,126,255]` | `[17281,0,16238,65535]` |
| `(898,670)` | `export-quantization` | `[88,0,175,255]` | `[11280,0,22529,65535]` |

For the three classified pixels, the Windows byte matches the lower
`floor(word * 255 / 32768)`-style export rule applied to the sampled store word.
The `(907,222)` pixel remains unresolved because the simple export-quantization
model does not explain B=0 from sampled store word 129 without a direct Windows
PF16 store/export stop.

## Decision

- Do not retune field topology, source-mask ownership, or broad compose logic from
  the `case_0024..0027` max=1 family.
- Treat the family as export-quantization-first.
- If this family needs more proof, request only the direct Windows PF16
  store/export stop for `(907,222)`.
- Otherwise move DG work to the separate broad Layer-source family
  `case_0012/0013/0014`, keeping `case_0016/0028` as smaller separate families.

## Verification

Commands run:

```sh
python3 scripts/intake_olm_return.py /Volumes/onmk/olm_pr/new/olm_runtime_trace_olmdistancegradation_depthgate_quantization_witness_20260708_return_windows_20260708.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md --runtime-comparison-dir refs/reports/runtime_trace_comparisons
python3 scripts/analyze_pending_runtime_trace_packages.py --package-dir refs/runtime_trace_packages --output-json refs/reports/pending_runtime_trace_packages.json --output-md refs/reports/pending_runtime_trace_packages.md
```

Result:

- Runtime trace return verified as `answered`.
- Pending runtime trace packages after intake: `0`.
