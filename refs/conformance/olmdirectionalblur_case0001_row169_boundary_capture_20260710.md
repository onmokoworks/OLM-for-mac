# OLMDirectionalBlur case_0001 row169 boundary capture

- Status: `ok`
- Lane: source 959 -> row 169 targets `(494,169)` and `(579,169)`
- No Mac source or PNG tuning performed.

## Classification

| target | post B RGB | post denom | post alpha/valid | write count | writeback B RGB | classification |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `(494, 169)` | `[0.0, 0.0, 0.0]` | 1 | 1 | 4 | `[0.0, 0.0, 0.0]` | `scatter_write_zero_rgb` |
| `(579, 169)` | `[0.0, 0.0, 0.0]` | 1 | 1 | 4 | `[0.0, 0.0, 0.0]` | `scatter_write_zero_rgb` |

## Capture Contract

Each record includes the typed scatter arguments, A/B/denom/alpha_or_valid immediately after scatter, and the same arrays after FUN_1800038d0 returns. Final stored bytes are intentionally outside this rowdriver-only probe.
