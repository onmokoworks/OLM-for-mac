# OLMDistanceGradation 16bpc Constant Binary Threshold Fix (2026-06-29)

- Before: `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424/reports/ae_pixel_16bpc_extended_powerfix.json`
- After: `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_constant_binary_20260629_1454/reports/ae_pixel_16bpc_extended_constant_binary.json`
- Exact: `1/16`

## Changed Cases

| Case | max before -> after | mean before -> after | nonzero_px before -> after |
| --- | ---: | ---: | ---: |
| `olmdistancegradation_extended__case_0020` | 61165 -> 61165 | 14.4223 -> 0.0144 | 1001 -> 1 |
| `olmdistancegradation_extended__case_0021` | 61165 -> 61165 | 14.4367 -> 0.0144 | 1002 -> 1 |
| `olmdistancegradation_extended__case_0022` | 61165 -> 61165 | 134.6708 -> 2.7663 | 9347 -> 192 |
| `olmdistancegradation_extended__case_0023` | 61165 -> 61165 | 19.9982 -> 1.0518 | 1388 -> 73 |

## Reading

- `FUN_181174760` uses the Constant-specific binary threshold path (`THRESH_BINARY`) while non-Constant paths keep truncation/normalization.
- The fix moves `case_0020` from `1001` changed pixels to `1`, `case_0021` from `1002` to `1`, `case_0022` from `9347` to `192`, and `case_0023` from `1388` to `73`.
- Non-Constant residual families are unchanged; continue with Layer/no-bg source ownership and Sphere/Power boundary quantization separately.
- The remaining Constant/background pixels still select the opposite endpoint, so this family is improved but not AE exact.
