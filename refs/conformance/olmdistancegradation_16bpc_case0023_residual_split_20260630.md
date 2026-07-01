# OLMDistanceGradation 16bpc case_0023 Residual Split - 2026-06-30

Residual classification for the current Mac single-case output after the no-post-threshold control probe.

- Residual pixels: `73`
- Residual bbox: `61,7 .. 1910,895`

| Inside raw EDT | Count | Outside raw EDT values | Candidate RGBA counts | Reference RGBA counts |
| ---: | ---: | --- | --- | --- |
| `1.000000` | 65 | `[0.0]` | `7195,0,61165,65535` x65 | `65535,0,0,65535` x65 |
| `36.013885` | 8 | `[0.0]` | `65535,0,0,65535` x8 | `7195,0,61165,65535` x8 |

## Reading

- All 73 residual pixels stay inside the source alpha region: outside raw EDT is always `0.0`.
- The residual splits cleanly into two inside-distance buckets only:
  - `65px` at `inside EDT = 1.0`, where the current Mac output stays on the Gradation-color endpoint while Windows uses the BG-color endpoint.
  - `8px` at `inside EDT = 36.013885...`, just beyond the configured `Inside Threshold = 36`, where the endpoint choice flips the other way.
- That pattern is much more consistent with unresolved field-prep threshold / plateau ownership inside the `Both` Constant helper than with final writeback or a broad compose bug.
