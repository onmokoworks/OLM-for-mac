# OLMDistanceGradation 16bpc Power Param Fix (2026-06-29)

Status: `not-ae-exact`, but one real implementation bug is fixed.

## Bug

`Power` was read from a `PF_ADD_FLOAT_SLIDERX` parameter as:

```cpp
p->power = (float)FIX_2_FLOAT(params[DG_POWER]->u.fs_d.value);
```

That was wrong. `fs_d.value` is already the floating value. Applying
`FIX_2_FLOAT` divided it by 65536.

For `olmdistancegradation_extended__case_0026`, AE set `Power=2.59740734100342`,
but the plug-in used `3.96332907e-05`. That made `pow(field_x, power)` nearly
`1.0` everywhere, explaining the previous Gradation Color saturation.

## Evidence

- Before fix debug dump:
  `refs/reports/ae_single_case_olmdistancegradation_case0026_debugdump_20260629_1420/field_debug.txt`
- After fix debug dump:
  `refs/reports/ae_single_case_olmdistancegradation_case0026_powerfix_20260629_1422/field_debug.txt`
- Extended 16bpc rerun:
  `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424/reports/ae_pixel_16bpc_extended_powerfix.json`

The field itself was already correct on the row-0 witness before the fix:

| x | field_x |
| ---: | ---: |
| 0 | 1 |
| 1 | 1 |
| 2 | 1 |
| 3 | 0.923076928 |
| 4 | 0.846153855 |
| 5 | 0.769230783 |
| 6 | 0.692307711 |
| 7 | 0.615384638 |
| 8 | 0.538461566 |
| 9 | 0.461538464 |
| 10 | 0.384615391 |
| 11 | 0.307692319 |
| 12 | 0.230769232 |
| 13 | 0.15384616 |
| 14 | 0.0769230798 |

After the fix, the same row recovers the Windows ramp within tiny channel
deltas:

| x | Windows reference | Mac after fix | delta |
| ---: | --- | --- | --- |
| 3 | `[18147,0,49681,65535]` | `[18147,0,49685,65535]` | `[0,0,4,0]` |
| 4 | `[27731,0,39633,65535]` | `[27733,0,39633,65535]` | `[2,0,0,0]` |
| 5 | `[36021,0,30941,65535]` | `[36023,0,30941,65535]` | `[2,0,0,0]` |
| 6 | `[43085,0,23533,65535]` | `[43089,0,23533,65535]` | `[4,0,0,0]` |

## Current Gate

The 16bpc extended batch is still not exact:

| group | exact | fail | missing | total |
| --- | ---: | ---: | ---: | ---: |
| extended 16bpc after Power fix | 1 | 15 | 0 | 16 |

`case_0026` improved from a full saturation family to:

- `max_diff=11480`
- `mean_diff=2.925372`
- `nonzero_px=902747`

The remaining high-delta pixels are sparse boundary/source ownership cases, not
the global Power collapse.

## Next

Classify the remaining residuals by case family:

- `case_0020..0023`: Constant/background binary branch still has full-color
  sparse pixels.
- `case_0024..0028`: Power/layer/background cases now need field quantization,
  source ownership, and final compose/writeback proof.
- Do not revert the Power fix and do not retune background compose from the old
  saturated output.
