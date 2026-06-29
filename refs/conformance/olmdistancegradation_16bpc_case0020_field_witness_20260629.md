# OLMDistanceGradation 16bpc Case 0020 Field Witness (2026-06-29)

- Case: `olmdistancegradation_extended__case_0020`
- Family: `constant-bg-binary-sparse-full-color`
- Mac AE run: `refs/reports/ae_single_case_olmdistancegradation_case0020_pointdebug_20260629_1445`
- Installed plug-in SHA-256: `b08073b744f29d22b477461d47e46525b8145cfb80cac067bad6ff728340a430`
- Parameters observed in plug-in: `invert=0 in_out=1 inside=78 outside=204 render_mode=1 use_bg=1 interp=1 power=1 blur_mode=1 blur_size=0`

## Pixel Evidence

| Point | Mac field_x | Windows ref | Mac candidate | Delta |
| --- | ---: | --- | --- | --- |
| `(951,417)` | `1` | `[7195, 0, 61165, 65535]` | `[65535, 0, 0, 65535]` | `[58340, 0, -61165, 0]` |
| `(950,417)` | `0.999095619` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(951,416)` | `0.987179458` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(951,418)` | `1` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[0, 0, 0, 0]` |
| `(0,0)` | `0` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` |

## Reading

- This is not a final 16bpc writer issue. The wrong pixel is already decided by the pre-compose field value.
- The local Constant/background branch selects the red endpoint at `field_x == 1`, while adjacent `field_x < 1` points select the blue endpoint and match Windows.
- The next proof should inspect field normalization / exact distance maximum ownership around the local full-distance plateau, not color writeback or Power handling.
