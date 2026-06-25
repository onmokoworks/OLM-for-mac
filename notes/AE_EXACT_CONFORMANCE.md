# AE Exact Conformance Policy

This is the current correctness policy for the OLM Tools macOS port.

## Goal

The final target is AE-host output equivalence against the original Windows OLM
AEX, using Windows AE Software render as the reference path.

`AE exact` means the same input, same effect parameters, same AE/project
settings, and same bit depth produce a zero-diff Mac AE render against the
Windows AE Software reference.

## Status Vocabulary

Use these terms in progress notes, dashboards, and release communication:

| Status | Meaning | Release meaning |
| --- | --- | --- |
| `AE exact` | Mac AE render matches Windows AE Software reference with zero diff for the declared bit depth and case set. | Completed for that feature/bit-depth slice. |
| `CLI exact` | AE-free CLI output matches the Windows reference with zero diff. | Strong intermediate proof; not final completion. |
| `binary-grounded` | Ghidra/objdump/runtime trace proves the constants, branches, rounding, bounds, or sampling rule. | Required evidence for algorithm claims. |
| `guarded` | A regression gate passes with nonzero tolerance or known residuals. | Not complete. |
| `known-red` | A checked case is intentionally red and preserved as a regression/proof target. | Not complete. |
| `reference-generation split` | A case differs against a superseded or legacy reference, but matches the canonical normalized/current reference. | Not a compatibility failure; keep the reference sets separated. |
| `blocked` | PNG-only tuning is unsafe; needs asm/runtime trace/AE-host reference. | Do not tune blindly. |
| `off-by-1 candidate` | `max_diff <= 1`, but not AE exact. | Not complete; investigate rounding/quantization. |
| `synthetic probe` | A helper or synthetic fixture checks a local invariant rather than a Windows AE reference. | Not a compatibility claim. |

Do not use percent complete, `green`, or `complete-ish` as correctness claims.
Passing a smoke only means the current regression gate behaved as expected.

Keep the axes separate:

- `reference_kind`: what is treated as the reference, such as Windows AE
  Software, CLI output, or a synthetic fixture.
- `runner_kind`: what produced the candidate output, such as Mac AE plug-in or
  Mac CLI.
- `result_status`: whether that exact pair is `AE exact`, `CLI exact`,
  `known-red`, `blocked`, `invalid`, or another diagnostic state.

## Reference Path

- The canonical reference path is Windows AE Software render.
- GPU/CUDA renders are excluded from exactness claims unless a separate GPU
  conformance profile is explicitly created.
- `ADBE Force CPU GPU` is metadata only. It must not be used to infer the real
  CPU/GPU execution path.
- Record AE version, project renderer, color management, bit depth, input PNG,
  parameter manifest, and output format with every reference set.

## Bit Depth Order

Conformance expands in this order:

1. `8bpc`
2. `16bpc`
3. `32bpc`

Use the same case IDs, inputs, and parameters across bit depths whenever
possible. A feature is not "all bit depth exact" until every declared bit-depth
profile is `AE exact`.

For `32bpc`, define the comparator before claiming completion. Prefer exact
float equivalence when the host/output format supports it; otherwise document
the epsilon as a compatibility exception, not as `AE exact`.

## Binary-Grounded IR Requirement

Every algorithm feature that reaches release status should have an IR note that
records:

- parameter normalization
- constants and lookup tables
- loop bounds
- sampling order
- boundary mode
- RGB/A processing order
- premultiply and unpremultiply behavior
- float/int conversions
- floor, ceil, round, truncate behavior
- clamp and output quantization
- the binary evidence used to justify the rule

PNG diffs can generate hypotheses. They do not, by themselves, define the
algorithm.

For work that happens before new Windows PNG/runtime returns arrive, use
`notes/FORECAST_FIRST_PORTING_POLICY.md`. Forecast work can narrow and implement
constrained hypotheses, but it cannot promote a slice to `AE exact`.

## Public Compatibility Guard

Public compatibility should be guarded by:

- binary-grounded IR notes
- Windows Software reference manifests
- reference images or documented reference acquisition steps
- AE-free CLI comparison tools
- AE-host validation steps
- bit-depth-specific conformance suites

A fork should only claim OLM compatibility for the feature/bit-depth slices that
pass the same conformance suite. GPU behavior and unverified bit depths must be
called out separately.
