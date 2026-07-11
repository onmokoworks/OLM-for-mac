# OLMDistanceGradation 16bpc Export/Rounding Residual Audit

Date: 2026-07-09

This audit reuses existing Mac AE candidate PNGs and Windows Software reference PNGs. It does not introduce an implementation change.

| Case | nonzero px | max true16 | mean true16 | channel max RGBA | even nonzero deltas | output-space RGB +/-2 diagnostic |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `case_0012` | 2948 | 2 | 0.001990500 | `[2, 2, 2, 2]` | `True` | max `2`, nonzero `155` |
| `case_0013` | 9006 | 2 | 0.005261622 | `[2, 2, 2, 2]` | `True` | max `2`, nonzero `5394` |
| `case_0014` | 9630 | 4 | 0.005750386 | `[4, 4, 4, 2]` | `True` | max `2`, nonzero `5852` |
| `case_0016` | 5373 | 2 | 0.003700569 | `[2, 2, 2, 0]` | `True` | max `0`, nonzero `0` |

## Delta Histograms

### case_0012
- R: 0:41, -2:2891, 2:16
- G: 0:352, -2:2596
- B: 0:351, -2:2596, 2:1
- A: 0:2793, -2:131, 2:24

### case_0013
- R: 0:3195, -2:4398, 2:1413
- G: 0:3698, -2:4091, 2:1217
- B: 0:3698, -2:4091, 2:1217
- A: 0:3612, 2:5394

### case_0014
- R: 0:3254, -2:4792, 2:1536, -4:48
- G: 0:3865, -2:4449, 2:1271, -4:45
- B: 0:3865, -2:4449, 2:1271, -4:45
- A: 0:3826, 2:5804

### case_0016
- R: 0:2, -2:5371
- G: 0:385, -2:4988
- B: 0:385, -2:4988
- A: 0:5373

## Max-Delta Examples

### case_0012
- `[438, 0]` src `[27769, 27769, 27769, 42661]` candidate `[42307, 42307, 42307, 64997]` reference `[42309, 42309, 42309, 64997]` diff `[-2, -2, -2, 0]`
- `[657, 0]` src `[56129, 56129, 56129, 60651]` candidate `[60151, 60151, 60151, 64997]` reference `[60153, 60153, 60153, 64997]` diff `[-2, -2, -2, 0]`
- `[625, 1]` src `[41939, 41939, 41939, 52427]` candidate `[51993, 51993, 51993, 64997]` reference `[51995, 51995, 51995, 64997]` diff `[-2, -2, -2, 0]`
- `[1034, 1]` src `[47457, 47457, 47457, 55769]` candidate `[55119, 55119, 55119, 64775]` reference `[55121, 55121, 55121, 64775]` diff `[-2, -2, -2, 0]`
- `[1035, 1]` src `[45723, 45723, 45723, 54741]` candidate `[54103, 54103, 54103, 64775]` reference `[54105, 54105, 54105, 64775]` diff `[-2, -2, -2, 0]`

### case_0013
- `[15, 0]` src `[7451, 7451, 7451, 22101]` candidate `[7309, 7309, 7309, 21683]` reference `[7311, 7311, 7311, 21683]` diff `[-2, -2, -2, 0]`
- `[16, 0]` src `[11321, 11321, 11321, 27241]` candidate `[11107, 11107, 11107, 26727]` reference `[11109, 11109, 11109, 26727]` diff `[-2, -2, -2, 0]`
- `[17, 0]` src `[3273, 3273, 3273, 14649]` candidate `[3211, 3211, 3211, 14373]` reference `[3211, 3211, 3211, 14371]` diff `[0, 0, 0, 2]`
- `[438, 0]` src `[27769, 27769, 27769, 42661]` candidate `[27245, 27245, 27245, 41857]` reference `[27245, 27245, 27245, 41855]` diff `[0, 0, 0, 2]`
- `[439, 0]` src `[65023, 65023, 65023, 65279]` candidate `[62569, 62569, 62569, 62815]` reference `[62567, 62567, 62567, 62813]` diff `[2, 2, 2, 2]`

### case_0014
- `[448, 0]` src `[20035, 20035, 20035, 36237]` candidate `[19985, 19985, 19985, 36151]` reference `[19989, 19989, 19989, 36151]` diff `[-4, -4, -4, 0]`
- `[752, 10]` src `[20035, 20035, 20035, 36237]` candidate `[19985, 19985, 19985, 36151]` reference `[19989, 19989, 19989, 36151]` diff `[-4, -4, -4, 0]`
- `[1371, 10]` src `[20035, 20035, 20035, 36237]` candidate `[19985, 19985, 19985, 36151]` reference `[19989, 19989, 19989, 36151]` diff `[-4, -4, -4, 0]`
- `[1424, 11]` src `[20035, 20035, 20035, 36237]` candidate `[19985, 19985, 19985, 36151]` reference `[19989, 19989, 19989, 36151]` diff `[-4, -4, -4, 0]`
- `[1734, 17]` src `[20035, 20035, 20035, 36237]` candidate `[19985, 19985, 19985, 36151]` reference `[19989, 19989, 19989, 36151]` diff `[-4, -4, -4, 0]`

### case_0016
- `[15, 0]` src `[7451, 7451, 7451, 22101]` candidate `[7449, 7449, 7449, 22101]` reference `[7451, 7451, 7451, 22101]` diff `[-2, -2, -2, 0]`
- `[17, 0]` src `[3273, 3273, 3273, 14649]` candidate `[3271, 3271, 3271, 14649]` reference `[3273, 3273, 3273, 14649]` diff `[-2, -2, -2, 0]`
- `[441, 0]` src `[10899, 10899, 10899, 26727]` candidate `[10897, 10897, 10897, 26727]` reference `[10899, 10899, 10899, 26727]` diff `[-2, -2, -2, 0]`
- `[448, 0]` src `[20035, 20035, 20035, 36237]` candidate `[20033, 20033, 20033, 36237]` reference `[20035, 20035, 20035, 36237]` diff `[-2, -2, -2, 0]`
- `[1653, 0]` src `[8715, 8715, 8715, 23901]` candidate `[8713, 8713, 8713, 23901]` reference `[8715, 8715, 8715, 23901]` diff `[-2, -2, -2, 0]`

## Reading

- The residual is entirely even-valued in these four focused cases, consistent with a 16bpc store/export quantization or PNG decode/encode scale family rather than a new broad source-ownership rule.
- case_0014 is the only focused case with RGB abs delta 4; examples are retained so a future proof can target one -4 pixel instead of a broad rerender.
- The output-space +/-2 diagnostic is not an implementation rule because it uses reference direction; it is only a bound showing the remaining family is tiny and direction-dependent.

## Decision

- Do not change `mac/OLMDistanceGradation` from this audit alone.
- The next proof should target one representative `case_0012` +/-2 pixel and one `case_0014` -4 RGB pixel at the store/export boundary, or run a Mac AE same-run debug export that proves whether the PF16 store already contains the Windows word.
