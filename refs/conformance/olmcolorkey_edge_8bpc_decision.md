# OLMColorKey Edge Decision Matrix

- Decision: `preserve-normalized-ae-exact`
- Recommended action: Do not tune Edge Blur from the 20260604 case_0009 residual. Preserve normalized 20260618 Software exactness for 8bpc; 16bpc Windows references are covered and now need Mac AE comparison.

## Evidence

- Normalized 8bpc: `normalized-software-exact` (9/9 exact)
- Windows 16bpc reference: `reference-covered-compare-pending` (9 cases)
- Legacy split: `reference-generation-split` (legacy max `47`)
- Runtime trace: `not-actionable` (focus `await-windows-trace`)

## Legacy Drift Cases

| Case | Max | Mean | Witness |
| --- | ---: | ---: | --- |
| `case_0009` | 47 | 0.069921031 | `x=1678 y=722 c=3 ref=[0, 0, 0, 136] cand=[0, 0, 0, 89]` |

## Next Evidence

- Preserve Mac AE exact behavior against canonical normalized 8bpc ColorKey refs.
- Run Mac AE-host 16bpc validation against the covered Windows Software reference cases.
- 32bpc Software reference coverage for core and Edge paths.
- Only request narrow Edge runtime trace if a current normalized Software residual reappears.
