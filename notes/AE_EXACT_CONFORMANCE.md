# AE Exact Conformance Policy

This is the current correctness policy for the OLM Tools macOS port.

## Goal

The final target is AE-host output equivalence against the original Windows OLM
AEX, using Windows AE Software render as the reference path.

`AE exact` means the same input, same effect parameters, same AE/project
settings, and same bit depth produce a zero-diff Mac AE render against the
Windows AE Software reference.

The target plug-in set, critical-path ordering, and release gate are defined in
`notes/PORTING_ROADMAP.md`. The machine-readable completion population lives in
`refs/conformance/olm_release_scope.json`; check it with:

```bash
python3 scripts/check_olm_release_scope.py
```

An `AE exact` feature/depth slice is not the same as a complete plug-in. Release
completion additionally requires every declared feature/path/depth cell, stable
host integration, complete binary-grounded IR, manifests, and reproducible
comparators. `ColorKeep` is currently support-only and excluded from that
release population. `OLMSmoother v1` remains in the population with an explicit
endgame policy decision still required.

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
| `host-version split` | A no-effect render differs because the AE version, platform, color-management, or EXR path differs. | Not a plug-in failure and not an `AE exact` verdict; align the host profile first. |
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

| Host status | Meaning | AEで今やってよいこと |
| --- | --- | --- |
| `host-blocked` | Plug-in fails to load, add, set basic params, or render a frame reliably. | 読み込み・追加・クラッシュだけを直す。見た目合わせはしない。 |
| `host-smoke` | Plug-in loads and can render a minimal frame, but output is not yet trusted. | UI配線、パラメータ反映、クラッシュだけを確認する。 |
| `host-debuggable` | Plug-in can be manipulated in AE without obvious host failure, but algorithm output is still not trusted. | 指定したwitnessピクセルや分岐だけを確認する。自由な見た目合わせはしない。 |
| `host-visual-tuning-ready` | Binary/CLI evidence is strong enough that AE visual comparison can safely refine residuals. | 狭い残差の確認・修正に使える。 |
| `host-stable` | Manual use is stable across the currently supported feature slice. | 対応済みsliceの広めの回帰確認に使える。 |

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

## Current OLMSmoother2 Exact Slices

- The current-AEX legacy/key/gamma 8bpc suite is Mac AE `12/12`,
  `max_diff=0`.
- The declared Preserve-RGB 16bpc case-01..10 set is raw FLOAT32 exact for
  both its no-effect controls and effect-on outputs: all 20 gates are
  `0/8,294,400` mismatched words with max raw u32 delta `0`. Each case uses
  one Windows `aerender` process with two AEP-embedded render-queue items and
  a hash-bound fresh Mac footage path.
- The declared Preserve-RGB 32bpc case-01..10 set is raw FLOAT32 exact for
  both its no-effect controls and effect-on outputs: all 20 gates are
  `0/8,294,400` mismatched words with max raw u32 delta `0`. Cases 01–06,
  08, and 10 use one Windows `aerender` process per case with two
  AEP-embedded render-queue items and the exact hash-bound Mac input. Cases
  07 and 09 retain their independent binary/runtime-grounded closeouts.
- The final 8/16/32bpc `-O2` binary is
  `bad3472d3ce808bdd69f0fa55be493c3d2f76cd7ad8c49b519f03347b3e2cd7b`;
  among its grounded fixes, actual-AEX `DIVSS` reciprocal sequencing is
  preserved before exponent promotion, and PF16 composite accumulation uses
  the Windows-separated scalar multiply/add order.
- The final binary preserves the frozen 8bpc suite at `12/12`,
  `max_diff=0`, and the declared 32bpc set at all 20 raw gates.

Evidence:
`refs/conformance/olmsmoother2_16bpc_case01_10_ae_exact_20260727.md`,
`refs/conformance/olmsmoother2_case07_16bpc_mac_ae_exact_20260727.md`,
`refs/conformance/olmsmoother2_case07_32bpc_mac_ae_exact_20260727.md`, and
`refs/conformance/olmsmoother2_case09_32bpc_mac_ae_exact_20260727.md`, and
`refs/conformance/olmsmoother2_32bpc_case01_10_ae_exact_20260727.md`.

## Current OLMBlur Exact Slices

- The declared 32bpc `case_0001` and `case_0002` profiles at Blur Amount
  `129.4`, Smoothness `100`, Legacy `0`, and respectively Repeat/Bias `1/1`
  and `2/2` are AE exact. Windows and Mac
  AE `26.3x87` render the same path-normalized `32bpc` Software AEPX with
  uncompressed FLOAT EXR effect/control queue items.
- For each case, the no-effect control and effect-on comparisons are both
  `0/8,294,400` mismatched FLOAT32 words with max raw u32 delta `0`.
- Windows Kernel Process ETW binds the live `AfterFX.com` child to loaded
  `OLMBlur.aex` SHA-256 `f0611785...e96e5b`; the Mac plug-in Mach-O SHA-256
  is `71df7efc...f4f0d72`.
- This is a two-case 32bpc promotion. It does not promote untested OLMBlur
  32bpc cases or replace the existing 8/16bpc declared-case records.

Evidence:
`refs/conformance/olmblur_32bpc_case0001_ae_exact_20260727.md` and
`refs/conformance/olmblur_32bpc_case0002_ae_exact_20260727.md`.

## Reference Path

- The canonical reference path is Windows AE Software render.
- GPU/CUDA renders are excluded from exactness claims unless a separate GPU
  conformance profile is explicitly created.
- `ADBE Force CPU GPU` is metadata only. It must not be used to infer the real
  CPU/GPU execution path.
- Record AE version, project renderer, color management, bit depth, input PNG,
  parameter manifest, and output format with every reference set.
- For float-preserving 32bpc comparisons, the AE host version and a no-effect
  EXR control are also part of the comparison profile. If the no-effect control
  differs, classify the pair as `host-version split`; do not attribute an
  effect-output residual to the plug-in or correct it with a compensating
  gamma transform.

## Bit Depth Order

Conformance expands in this order:

1. `8bpc`
2. `16bpc`
3. `32bpc`

Use the same case IDs, inputs, and parameters across bit depths whenever
possible. A feature is not "all bit depth exact" until every declared bit-depth
profile is `AE exact`.

Reference image format policy:

- `8bpc`: PNG is acceptable for exact image references.
- `16bpc`: prefer TIFF or EXR for newly captured references. PNG may remain in
  older fixture bundles as reproduction context, but a PNG-only rerender should
  not override a typed PF16 store/export witness.
- `32bpc`: use EXR or another float-preserving format. PNG-only 32bpc returns
  are probe/smoke evidence only and cannot establish `AE exact`.

For `32bpc`, define the comparator before claiming completion. Prefer exact
float equivalence when the host/output format supports it; otherwise document
the epsilon as a compatibility exception, not as `AE exact`.

Before comparing a 32bpc effect case, render the corresponding
`before_effects` artifact through the same Mac AE import/project/output path.
It must be exact to the Windows no-effect artifact for the host profile in
use. A no-effect mismatch blocks effect attribution even when both EXRs are
valid FLOAT files.

## Why Bit Depths Diverge

Different bit depths are not just "the same algorithm with a larger number
range". They often exercise different internal behavior:

- `8bpc` can hide tiny float-state differences because everything is quantized
  early into bytes.
- `16bpc` often exposes half-step and writer-boundary differences because AE
  stores `PF_Pixel16` words while many plug-ins still compute in float and only
  quantize at the end.
- `32bpc` can expose whether the plug-in really preserves float-domain behavior
  such as premultiply/unpremultiply order, accumulator precision, clamp timing,
  denormal handling, and whether the algorithm silently depends on integer
  truncation that was invisible at lower bit depths.

Common sources of bit-depth drift:

- different writeback rules (`floor(x + 0.5)`, ties-to-even, truncate)
- different clamp points
- float vs integer intermediates
- premultiply/unpremultiply at different stages
- alpha-weight normalization differences
- lookup tables or thresholds scaled differently per bit depth
- host callback differences between 8/16/32bpc paths
- old AEX codepaths that branch by pixel format

So yes: expanding a plug-in across `8bpc -> 16bpc -> 32bpc` usually gives a
truer picture of whether the Mac port matches the Windows AEX, not just whether
the current PNG set happens to look right.

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

## UI Parameter Schema Boundary

Visible AE parameter definitions should be grounded separately from algorithm
behavior.

- Defaults, hard min/max, UI min/max, control types, and popup choices should
  come from the plug-in source `PF_ADD_*` definitions when available.
- Current source-backed extraction report:
  `refs/reports/mac_plugin_param_schema_20260629.md` and
  `refs/reports/mac_plugin_param_schema_20260629.json`.
- Windows cold-start defaults should be captured separately when possible.
  Current all-plugin fresh-instance request:
  `refs/reference_requests/olm_fresh_instance_defaults_20260629.json`.
- The source-of-truth split between source-backed schema, Windows fresh default
  capture, and per-case manifests is recorded in
  `notes/PARAMETER_SOURCE_OF_TRUTH.md`.
- This report is authoritative for "what values can the user set?" and "what
  is the default UI state?".
- It is not sufficient evidence for `AE exact`, because it does not prove the
  internal response curve, hidden branches, float/int conversion behavior, or
  final writeback path.

When a mismatch is suspected, first separate:

1. Was the same UI parameter state applied?
2. Does the same parameter state produce the same internal/output behavior?

Do not use PNG differences alone to answer question 1 when the source-backed
schema is available.

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
