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

Keep the three planning axes separate:

- `correctness_status`: whether the algorithm output is correct against the
  Windows AE Software reference for a declared slice.
- `host_status`: whether the Mac AE plug-in is usable enough to make hands-on
  AE testing meaningful.
- `work_lane`: the next kind of work that is allowed for the slice.

`AE exact`, CLI parity, AE manual testing, and runtime trace waits must not be
merged into a single progress word.

Use these `correctness_status` labels:

| correctness_status | Meaning |
| --- | --- |
| `AE exact` | Mac AE render matches Windows AE Software reference with zero diff for the declared bit depth and case set. |
| `CLI exact` | AE-free CLI output matches the Windows reference with zero diff. |
| `binary-grounded` | Ghidra/objdump/runtime trace proves the relevant rule, but the declared slice is not necessarily exact yet. |
| `guarded` | A nonzero residual or tolerance is intentionally preserved as a regression/proof target. |
| `known-red` | A checked case is expected to fail and is kept to prevent accidental reclassification. |
| `blocked` | PNG-only tuning is unsafe; more binary/runtime/AE-host proof is required. |

Keep host usability separate from correctness:

- `host_status`: whether the Mac AE plug-in currently loads, exposes usable UI,
  accepts manual parameter changes, and finishes a render without host errors.
- A feature can be `AE exact` for a packaged case set and still be poor in
  manual host usability.
- A feature can be host-usable enough to debug while still being far from
  `AE exact`.

Use these host-side labels when discussing whether AE hands-on testing is worth
doing yet:

| Host status | Meaning | When AE manual testing is useful |
| --- | --- | --- |
| `host-blocked` | Plug-in fails to load, add, set basic params, or render a frame reliably. | Only for host integration debugging. Not for visual tuning. |
| `host-smoke` | Plug-in loads and can render a minimal frame, but output is not yet trusted. | Only for parameter wiring and crash checks. |
| `host-debuggable` | Plug-in can be manipulated in AE without obvious host failure, but algorithm output is still not trusted. | For bounded witness checks, not freeform look-matching. |
| `host-visual-tuning-ready` | Binary/CLI evidence is strong enough that AE visual comparison can safely refine residuals. | Yes, for narrow residual tuning. |
| `host-stable` | Manual use is stable across the currently supported feature slice. | Safe for broader hands-on validation. |

Use these `work_lane` labels to choose the next action:

| work_lane | Meaning | Allowed work |
| --- | --- | --- |
| `host-fix` | AE load/add/parameter/render behavior is broken or untrusted. | Fix host integration before visual or exactness tuning. |
| `binary-proof` | The next useful evidence must come from asm, objdump, Ghidra, or runtime trace. | Narrow witness design, static analysis, trace intake, and proof-backed implementation. |
| `cli-port` | The algorithm is constrained enough to implement and test outside AE. | CLI implementation and reference comparison. |
| `ae-validate` | The implementation is ready for Mac AE output comparison. | AE-host render, exact comparison, and narrow residual classification. |
| `bitdepth-expand` | A lower bit-depth slice is exact and should be expanded to 16/32bpc. | Generate/ingest bit-depth references and compare by bit-depth policy. |
| `parked` | Current work would mostly become PNG-only guessing. | Wait for a sharper witness, proof, or user priority change. |

Default next-action priority:

1. If any active target is `host-blocked`, prefer `host-fix`.
2. Preserve existing `AE exact` slices; route them to `bitdepth-expand` instead
   of broad rewrites.
3. Do not visually tune `blocked` or `host-smoke` hard paths from broad PNGs.
4. When runtime trace is needed, define a narrow witness before packaging work.
5. Treat `CLI exact` as intermediate evidence, not Mac AE completion.
6. Manual AE checks are useful only at `host-debuggable` or better, and should
   be tied to a witness unless the slice is `host-stable`.

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
