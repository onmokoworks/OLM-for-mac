# OLMBlur Decision Matrix

- Decision: `preserve-normalized-ae-exact`
- Recommended action: Do not tune OLMBlur from the old 20260604 drift or from AE-free CLI max=1 witnesses. The current trace points at accumulation/helper state before byte output, while packaged 8bpc AE slices are exact; 16bpc Windows references are covered and now need Mac AE comparison.

## Evidence

- Normalized 8bpc: `normalized-software-exact` (7/7 exact)
- Windows 16bpc reference: `reference-covered-compare-pending` (7 cases)
- Legacy drift: `normalized-software-exact-with-legacy-drift` (4 cases)
- CLI residuals: `diagnostic-max1` (max `1`, nonzero px `4`)
- Runtime trace: `prewriteback-or-helper-state` (focus `nonlegacy-accumulation-or-writeback`)

## Runtime Witness Classification

- `case_0006`: Windows pre-writeback `['0x1.72fffe0000000p+7', '0x1.44a3c20000000p-4', '0x1.44a3c20000000p-4']`, Mac CLI pre-writeback `['0x1.73p+7', '0x1.44a3c6p-4', '0x1.44a3c6p-4']`.
- `case_0007`: writer family `OLMBlur+0x7FDF`; Legacy border/all-same state is not isolated.

## Legacy Drift Cases

| Case | Max | Mean | Witness |
| --- | ---: | ---: | --- |
| `case_0001` | 59 | 1.287920525 | `x=476 y=197 c=0 ref=[225, 0, 0, 255] cand=[166, 0, 0, 255]` |
| `case_0002` | 59 | 1.287920525 | `x=476 y=197 c=0 ref=[225, 0, 0, 255] cand=[166, 0, 0, 255]` |
| `case_0003` | 14 | 1.727592593 | `x=0 y=0 c=0 ref=[8, 0, 0, 255] cand=[22, 0, 0, 255]` |
| `case_0004` | 58 | 1.268115355 | `x=479 y=200 c=0 ref=[229, 0, 0, 255] cand=[171, 0, 0, 255]` |

## Next Evidence

- Packaged Mac AE exact against canonical normalized 8bpc OLMBlur refs is already established; preserve it.
- Run Mac AE-host 16bpc validation against the covered Windows Software reference cases.
- 32bpc Software reference coverage.
- Only continue CLI max=1 closure if binary-grounding the true accumulation/helper and Legacy border/all-same state becomes necessary.
