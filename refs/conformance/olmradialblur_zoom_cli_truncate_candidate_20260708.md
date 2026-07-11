# OLMRadialBlur Zoom CLI Truncate Candidate Probe

Date: 2026-07-08

## Verdict

`rejected_overbroad_alpha_truncation`

The truncate candidate moves the primary witness `(6,0)` to alpha `254`, but it is too broad: full-image diff worsens to `max=1 mean=0.0688 nonzero_px=567071` and many Windows-255 top-row pixels become 254 locally.

## Top Row Alpha Sample

| x | Windows | baseline | truncate candidate |
| ---: | ---: | ---: | ---: |
| 0 | 255 | 255 | 255 |
| 1 | 255 | 255 | 254 |
| 2 | 255 | 255 | 254 |
| 3 | 255 | 255 | 254 |
| 4 | 255 | 255 | 254 |
| 5 | 255 | 255 | 254 |
| 6 | 254 | 255 | 254 |
| 7 | 254 | 255 | 255 |
| 8 | 255 | 255 | 255 |
| 9 | 255 | 255 | 254 |
| 10 | 255 | 255 | 255 |
| 11 | 255 | 255 | 254 |
| 12 | 254 | 255 | 254 |
| 13 | 255 | 255 | 254 |
| 14 | 255 | 255 | 255 |
| 15 | 255 | 255 | 254 |
| 16 | 255 | 255 | 254 |
| 17 | 255 | 255 | 255 |
| 18 | 255 | 255 | 254 |
| 19 | 255 | 255 | 254 |
| 20 | 255 | 255 | 254 |
| 21 | 255 | 255 | 255 |
| 22 | 255 | 255 | 255 |
| 23 | 255 | 255 | 255 |
| 24 | 255 | 255 | 255 |
| 25 | 255 | 255 | 254 |
| 26 | 255 | 255 | 254 |
| 27 | 255 | 255 | 254 |
| 28 | 255 | 255 | 255 |
| 29 | 255 | 255 | 255 |
| 30 | 255 | 255 | 255 |
| 31 | 255 | 255 | 255 |

## Interpretation

The remaining rule is not a global alpha quantization epsilon. It is still tied to which final-polar cells become slightly below one, which points back to exact AEX polar cell coordinate/float sequence or plane selection. Keep this candidate as rejected evidence and do not promote it to Mac source.
