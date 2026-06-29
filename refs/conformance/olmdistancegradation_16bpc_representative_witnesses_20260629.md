# OLMDistanceGradation 16bpc Representative Witnesses (2026-06-29)

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Run dir: `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424`

## Cases

### olmdistancegradation_extended__case_0020

- Family: `constant-bg-binary-sparse-full-color`
- Changed pixels: `1001`
- Changed bbox: `[426, 417, 1919, 1079]`
- Changed input alpha unique count: `1`
- Changed reference alpha unique count: `1`
- Changed candidate alpha unique count: `1`

| Point | input | reference | candidate | delta |
| --- | --- | --- | --- | --- |
| `(951,417)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[58340, 0, -61165, 0]` |
| `(950,417)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(951,416)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(951,418)` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[0, 0, 0, 0]` |
| `(0,0)` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` |

### olmdistancegradation_extended__case_0012

- Family: `layer-no-bg-source-or-alpha-ownership`
- Changed pixels: `25421`
- Changed bbox: `[0, 0, 1919, 1079]`
- Changed input alpha unique count: `256`
- Changed reference alpha unique count: `1110`
- Changed candidate alpha unique count: `1107`

| Point | input | reference | candidate | delta |
| --- | --- | --- | --- | --- |
| `(462,7)` | `[16255, 16255, 16255, 32639]` | `[32371, 32371, 32371, 64997]` | `[16121, 16121, 16121, 64997]` | `[-16250, -16250, -16250, 0]` |
| `(72,8)` | `[16255, 16255, 16255, 32639]` | `[32371, 32371, 32371, 64997]` | `[16121, 16121, 16121, 64997]` | `[-16250, -16250, -16250, 0]` |
| `(462,6)` | `[65535, 65535, 65535, 65535]` | `[64461, 64461, 64461, 64461]` | `[64461, 64461, 64461, 64461]` | `[0, 0, 0, 0]` |
| `(462,8)` | `[0, 0, 0, 0]` | `[0, 0, 0, 64095]` | `[0, 0, 0, 64095]` | `[0, 0, 0, 0]` |
| `(0,0)` | `[0, 0, 0, 0]` | `[0, 0, 0, 43949]` | `[0, 0, 0, 43949]` | `[0, 0, 0, 0]` |

## Reading

- case_0020: Sparse Constant/background mismatch: candidate keeps the input/gradation red endpoint where Windows selects the blue background endpoint on a narrow opaque-source boundary.
- case_0012: Layer/no-bg mismatch: alpha is mostly shared, but Windows RGB is raised toward the post-compose alpha/source-owned value while the candidate keeps lower source RGB.
- Prefer case_0020 first: it is sparse, fully opaque, and separates branch/color selection from alpha ownership.
