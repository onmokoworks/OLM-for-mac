# OLMBlur 8bpc worker Mac AE validation

- Mac AE: `26.3x87`
- Project depth: explicitly forced `8bpc`
- Plug-in slice: actual-AEX-exact `FUN_180003710` Non-Legacy and
  `FUN_180007300` Legacy orchestration
- Renderer comparison: retained Windows Software reference families

## Result

| case | mode | normalized AE26.2 max | legacy AE25.2 max |
| --- | --- | ---: | ---: |
| 0001 | Non-Legacy | 59 | 0 |
| 0002 | Non-Legacy | 59 | 0 |
| 0003 | Legacy | 14 | 1 |
| 0004 | Non-Legacy | 58 | 0 |
| 0005 | Non-Legacy | 0 | 0 |
| 0006 | Non-Legacy | 0 | 0 |
| 0007 | Legacy | 0 | 0 |

All five Non-Legacy cases are byte-exact against the retained AE25.2 family.
The Legacy adapter now uses an actual-AEX complete-worker core that is exact on
three complete-buffer fixtures. Correcting the helper's decompiled `all_same`
branch to copy the current center source pixel makes case 0007 byte-exact
against both retained families. Case 0003 remains `max=1` over 10,752 pixels
against AE25.2 and `max=14` against AE26.2, so the full 8bpc cell is not exact.

## Classification

The Mac host adapter successfully preserves the complete-buffer AEX worker
result for its declared 8bpc Non-Legacy slice. Legacy case 0007 is host-exact;
case 0003 remains unresolved.
This does not choose the public
canonical Windows family because neither retained reference manifest records
the loaded AEX hash. The prepared hash-pinned current-AEX Windows recapture is
the deciding gate. Until it returns, this slice remains binary-grounded plus
host-validated against the legacy family, not a newly promoted canonical
`AE exact` cell.

The first batch attempted without a depth field is excluded because AE carried
16bpc from a prior render. This result uses the formal batch runner with
`project.bits_per_channel=8` explicitly present.
