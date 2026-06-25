# OLMDirectionalBlur Decision Matrix

- Decision: `blocked-await-runtime-or-asm-proof`
- Recommended action: Do not tune DirectionalBlur from broad PNG matrices. Need a typed angle-0 rowdriver/valid-alpha witness and a separate diagonal rotate-path sampler/validity witness before changing implementation.

## Candidate Matrix

- Best overall: `rotated-front-strength` mean `18.19779755015432` max `252`
- Best AEX-shaped: `rotated-aex-trunc-output` mean `22.066680169753084` max `251`
- Exact candidates: `[]`
- Warning: best overall candidates are measurement scaffolds; AEX-shaped candidates remain high residual

| Candidate | Mean sum | Max |
| --- | ---: | ---: |
| `rotated-front-strength` | 18.197798 | 252 |
| `direct` | 18.310725 | 253 |
| `rotated-aex-trunc-output` | 22.066680 | 251 |
| `rotated-aex-truncated-span` | 22.124634 | 251 |
| `rotated-aex-choreo` | 22.124938 | 251 |

## Residual Split

- Classification: `split-angle0-vs-diagonal`

| Case | Kind | Max | Mean | Witness |
| --- | --- | ---: | ---: | --- |
| `case_0001` | `angle0-rgb-only-rowdriver-or-valid-alpha` | 164 | 4.956985 | `[494, 169]` |
| `case_0005` | `diagonal-rgb-alpha-rotate-validity` | 251 | 2.297068 | `[507, 367]` |

## Runtime Trace

- Status: `answered_partial`
- Focus: `angle0:await-windows-trace; diagonal:await-windows-trace`
- Classification: `not-actionable`

## Next Evidence

- Successful runtime/asm proof for angle-0 case_0001 rowdriver accumulation or valid-alpha side channel.
- Successful runtime/asm proof for diagonal case_0005 rotate/sampler/validity path.
- Keep direct/rotated-front-strength as measurement baselines only, not implementation truth.
