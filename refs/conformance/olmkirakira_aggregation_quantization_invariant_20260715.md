# OLMKiraKira Aggregation and Final Quantization Invariant

Status: **local-invariant-proven**

## FACT

- Local merge-mode-1 RGB is checked as `glow_rgb * glow_alpha + source_rgb * (1 - glow_alpha)`.
- Alpha is checked as source-alpha passthrough.
- 8bpc output is checked as nearest integer quantization with clamping.
- Complete witness rows: `1`; passing rows: `1`.

## Witness checks

| Label | Status | Max float error | Predicted u8 | Observed u8 |
| --- | --- | ---: | --- | --- |
| `934,118` | `pass` | `2.8263381413040634e-08` | `[144, 144, 144, 255]` | `[144, 144, 144, 255]` |
| `960,540` | `incomplete` | `-` | `-` | `-` |
| `960,490` | `incomplete` | `-` | `-` | `-` |
| `1010,540` | `incomplete` | `-` | `-` | `-` |

## Evidence pairing

- Actual-AEX report: `refs/conformance/olmkirakira_mode3_forward_warp_contract_actual_aex_20260713.json` (`captured_forward_warp_contract`)
- OpenCV stage report: `refs/reports/runtime_trace_comparisons/olmkirakira_aggregation_compose_bt709_20260624.json` (`olmkirakira_stage_trace_comparison`)

## LIMIT

- This proves a local compose/quantization invariant for the complete Mac witness rows only.
- It does not claim AE exactness, Windows equivalence, or a correction to the remaining hotspot residual.
