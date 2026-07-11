# OLMBlur 16bpc complete-worker Mac AE validation

- Mac AE: `26.3x87`
- Project depth: request-fixed `16bpc`
- Mac binary SHA-256: `a320b41359be671babc6adb7ef7d37eaf507d639b7c69138adfafc6bbac9ae53`
- Non-Legacy core: actual AEX `FUN_180002280`, complete-buffer fixture exact
- Legacy core: actual AEX `FUN_180005f20`, three complete-buffer fixtures exact

## Result

| case | max diff | differing values | differing pixels |
| --- | ---: | ---: | ---: |
| 0001 | 0 | 0 | 0 |
| 0002 | 0 | 0 | 0 |
| 0003 | 0 | 0 | 0 |
| 0004 | 0 | 0 | 0 |
| 0005 | 0 | 0 | 0 |
| 0006 | 0 | 0 | 0 |
| 0007 | 0 | 0 | 0 |

The formal AE batch output is under
`/tmp/olmblur16_legacy_batch_20260711/results/bitdepth16_olmblur_exact`.
All seven declared 16bpc cases are byte-exact. The final case 0007 residual was
caused by the portable Legacy helper copying its comparison carry value in the
decompiled `all_same` branch. Actual AEX copies the current center source pixel.
After that binary-grounded correction, the 18 first-row pixels became exact.

## FACT / INFERENCE

- FACT: both portable 16bpc worker modes replay their declared actual-AEX
  complete-buffer fixtures byte-exact.
- FACT: the Mac AE formal batch is exact for cases 0001 through 0006.
- FACT: the formal Mac AE batch is byte-exact for all seven declared cases.
- RESULT: the declared OLMBlur 16bpc conformance cell is `AE exact`.
