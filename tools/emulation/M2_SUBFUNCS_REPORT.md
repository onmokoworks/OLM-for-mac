# Milestone 2 sub-function verification

- Binary: `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`

## M2 Check A: FUN_18000b680 (Gaussian kernel builder)

- n = 8, scalar `expf` path (DAT_18002b180 == 1)
- Expected (independent Python ref): `[1.0, 0.932103, 0.75484, 0.531096, 0.324653, 0.172422, 0.07956, 0.031895]`
- Got (emulator): `[1.0, 0.932103, 0.75484, 0.531096, 0.324653, 0.172422, 0.07956, 0.031895]`
- Max abs diff: 0.000e+00
- Imports exercised: ['expf']
- Instructions: 152
- **Result: PASS**

## M2 Check B: FUN_180001bb0 (corner-distance radii)

| cx | cy | w | h | expected (r1,r2) | got | ok |
|----|----|---|---|------------------|-----|----|
| 10.0 | 20.0 | 100 | 50 | (0, 94) | (0, 94) | yes |
| 90.0 | 5.0 | 100 | 50 | (0, 100) | (0, 100) | yes |
| -8.0 | 60.0 | 100 | 50 | (12, 123) | (12, 123) | yes |
| 50.0 | 25.0 | 100 | 50 | (0, 55) | (0, 55) | yes |

- **Result: PASS**

## Overall

- Check A (FUN_18000b680): PASS
- Check B (FUN_180001bb0): PASS
- **M2 sub-function verification: PASS**
