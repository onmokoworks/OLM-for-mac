# OLMDistanceGradation Decision Matrix

- Decision: `preserve-normalized-ae-exact`
- Recommended action: Do not tune DistanceGradation from legacy-only drift or AE-free CLI residuals. Preserve normalized 8bpc AE exact behavior and use binary/runtime evidence only if closing the CLI harness gap.

## Evidence

- Normalized 8bpc: `exact` (29/29 exact)
- Legacy drift: `normalized-software-exact-with-legacy-drift` (7 cases)
- Runtime trace: `not-actionable` (focus `await-windows-trace`)

## Legacy Drift Cases

| Feature | Case | Max | Mean | Witness |
| --- | --- | ---: | ---: | --- |
| `OLMDistanceGradation basic` | `case_0017` | 2 | 0.001613257 | `x=1046 y=102 c=0 ref=[4, 4, 4, 4] cand=[2, 2, 2, 4]` |
| `OLMDistanceGradation extended` | `case_0012` | 251 | 0.622667221 | `x=1697 y=12 c=0 ref=[253, 253, 253, 253] cand=[2, 2, 2, 253]` |
| `OLMDistanceGradation extended` | `case_0013` | 62 | 0.201817371 | `x=447 y=0 c=0 ref=[120, 120, 120, 120] cand=[58, 58, 58, 120]` |
| `OLMDistanceGradation extended` | `case_0014` | 63 | 0.204961058 | `x=447 y=0 c=0 ref=[122, 122, 122, 122] cand=[59, 59, 59, 122]` |
| `OLMDistanceGradation extended` | `case_0016` | 64 | 0.207432123 | `x=447 y=0 c=0 ref=[123, 123, 123, 123] cand=[59, 59, 59, 123]` |
| `OLMDistanceGradation extended` | `case_0027` | 6 | 0.001718147 | `x=397 y=281 c=0 ref=[255, 5, 5, 255] cand=[249, 0, 0, 255]` |
| `OLMDistanceGradation extended` | `case_0028` | 142 | 0.093512852 | `x=397 y=281 c=0 ref=[255, 141, 141, 255] cand=[113, 0, 0, 255]` |

## Next Evidence

- Preserve Mac AE exact behavior against canonical normalized 8bpc DistanceGradation refs.
- 16bpc and 32bpc Software reference coverage for basic, extended, and blur groups.
- Only request field-prep/OpenCV runtime trace if we decide to close AE-free CLI residuals or a current normalized residual reappears.
