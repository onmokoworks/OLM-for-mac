# OLMDistanceGradation BOTH add-vs-max overlap audit - 2026-07-07

This is a narrow local-model audit. It does not claim AE exact. It only
checks whether the existing 16bpc full-resolution masks expose a difference
between `max(inside, outside)` and `min(inside + outside, 1)` before any
future resize/downsample path is involved.

- Manifest: `refs/win_references/olm_bitdepth_16bpc_normalized_exact_20260625/OLMbit-depthconformancebatch/reference_manifest.json`
- BOTH cases checked: `11`
- Cases with add-vs-max divergence: `0`
- Total divergent pixels: `0`
- Decision: `no-current-fullres-add-vs-max-lever`

| Case | Interp | Blur | Inside | Outside | Divergent px | Max delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `olmdistancegradation_extended__case_0010` | 2 | 1 | 63 | 82 | 0 | 0 |
| `olmdistancegradation_extended__case_0011` | 2 | 1 | 348 | 0 | 0 | 0 |
| `olmdistancegradation_extended__case_0012` | 2 | 1 | 122 | 204 | 0 | 0 |
| `olmdistancegradation_extended__case_0021` | 1 | 1 | 78 | 402 | 0 | 0 |
| `olmdistancegradation_extended__case_0022` | 1 | 1 | 36 | 11 | 0 | 0 |
| `olmdistancegradation_extended__case_0023` | 1 | 1 | 36 | 0 | 0 | 0 |
| `olmdistancegradation_extended__case_0024` | 3 | 1 | 158 | 17 | 0 | 0 |
| `olmdistancegradation_extended__case_0025` | 3 | 1 | 158 | 13 | 0 | 0 |
| `olmdistancegradation_extended__case_0026` | 4 | 1 | 158 | 13 | 0 | 0 |
| `olmdistancegradation_extended__case_0027` | 4 | 1 | 158 | 13 | 0 | 0 |
| `olmdistancegradation_extended__case_0028` | 4 | 1 | 158 | 13 | 0 | 0 |

## Reading

- In the current full-resolution binary-mask model, inside/outside supports are complementary.
- Therefore `cv::add` and `max` do not diverge on these 16bpc BOTH cases.
- Keep the `cv::add` fact in the IR, but do not use it as an implementation lever for the current residuals unless a resize/downsample witness proves overlapping support.
