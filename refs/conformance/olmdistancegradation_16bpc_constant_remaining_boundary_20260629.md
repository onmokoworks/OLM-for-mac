# OLMDistanceGradation 16bpc Constant Remaining Boundary

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate dir: `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_constant_binary_20260629_1454/candidate`
- Conclusion: The remaining Constant-mode residuals after the binary-threshold fix are sparse and sit on distance-threshold boundary decisions. Treat them as OpenCV/AEX distanceTransform threshold ownership work, not compose/writeback tuning.

| Case | nonzero_px | max | mean | active side | active <=1px from threshold | nearest delta |
| --- | ---: | ---: | ---: | --- | ---: | ---: |
| `olmdistancegradation_extended__case_0020` | 1 | 61165 | 0.0144 | `inside` | 1 | 0.006410 |
| `olmdistancegradation_extended__case_0021` | 1 | 61165 | 0.0144 | `both-nearest` | 1 | 0.006410 |
| `olmdistancegradation_extended__case_0022` | 192 | 61165 | 2.7663 | `both-nearest` | 192 | 0.000000 |
| `olmdistancegradation_extended__case_0023` | 73 | 61165 | 1.0518 | `both-nearest` | 73 | 0.000000 |

## Witness Examples

### olmdistancegradation_extended__case_0020
- `(434,676)`: ref=[7195, 0, 61165, 65535] cand=[65535, 0, 0, 65535] inside=78.006410 outside=0.000000

### olmdistancegradation_extended__case_0021
- `(434,676)`: ref=[7195, 0, 61165, 65535] cand=[65535, 0, 0, 65535] inside=78.006410 outside=0.000000

### olmdistancegradation_extended__case_0022
- `(1101,55)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=0.000000 outside=10.770330
- `(1097,56)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=0.000000 outside=11.000000
- `(1408,62)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=0.000000 outside=11.000000
- `(1404,63)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=0.000000 outside=10.770330

### olmdistancegradation_extended__case_0023
- `(1699,7)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=1.000000 outside=0.000000
- `(985,26)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=1.000000 outside=0.000000
- `(1090,41)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=1.000000 outside=0.000000
- `(1097,45)`: ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] inside=1.000000 outside=0.000000
