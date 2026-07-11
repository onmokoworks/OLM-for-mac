# OLMDirectionalBlur Angle-0 Local Static Review

- Date: `2026-07-07`
- Scope: local-only review while waiting for
  `olmdirectionalblur_angle0_helper_gate_retry_20260702`
- Decision: `keep-blocked-await-typed-helper-witness`

## FACT

- Active structural base remains `rotated-aex-full-choreo`; broad
  `direct`, `rotated-front-strength`, prepass, scatter, and exact-rowdriver
  bundle candidates are diagnostics only, not implementation truth.
- The active angle-0 witness lane is `case_0001` on row `y=169`.
- Interior witness `(494,169)` has Windows reference `[164,0,0,255]` and
  current local candidate `[0,0,0,255]`; alpha already matches.
- Endpoint witness `(579,169)` is the right edge of the current local strip.
- The local full/scatter row segment for `case_0001` is `x=380..579`.
- Static AEX helper facts from `FUN_1800013e0` / `FUN_1800038d0` remain:
  front helper uses direction flag `param_3 = 1`, scales span as
  `trunc(param_9 * param_11)`, starts at offset `1`, loops while
  `offset < span`, and writes only to destination columns strictly left of the
  current source x. Rowdriver skips scatter when source A alpha is exactly
  zero.
- Therefore a same-row front-helper explanation for endpoint `(579,169)`
  requires a contributing source x greater than `579`. The visible same-row
  segment ending at `579` cannot explain that endpoint by itself.
- The current Windows package
  `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_angle0_helper_gate_retry_20260702.zip`
  includes the correct target witnesses `(494,169)` and `(579,169)`, the
  required denominator / `alpha_or_valid` / pre-writeback fields, and the
  rejection rules for broad `+0x2000` hit storms or final-byte-only answers.
- Current local CLI anchors in `cli/OLMDirectionalBlur/main.cpp` have drifted
  from older witness-prep line numbers. As of this review:
  - `render_rotated` signature starts at line `903`
  - noise/back unsupported guard is at lines `919..920`
  - alpha-fade gather setup starts at line `1040`
  - `source_driven_scatter` diagnostic branch starts at line `1146`
  - default row-scatter branch starts at line `1180`
  - same-row negative-shift branch for default `sample_sign=-1` uses
    `src_p = y * pad_w + (x + nshift)` at lines `1227..1231`
  - `rotated-aex-full-choreo` dispatch is at lines `1416..1417`
  - `rotated-aex-exact-scatter-helper` dispatch is at lines `1420..1421`
  - `rotated-aex-exact-rowdriver` dispatch is at lines `1422..1423`
  - `rotated-front-strength` dispatch is at lines `1462..1463`
  - `rotated-rowdriver-prepass` / `rotated-rowdriver-prepass-init` are at
    lines `1466..1469`

## INFERENCE

- The angle-0 residual is now narrower than a generic rowdriver bug. The useful
  split is:
  1. rowdriver/group membership differs, so Windows has a contributing
     helper-local source range that local reconstruction does not;
  2. a validity or alpha side channel contributes where the current local
     candidate treats the row as invalid/zero;
  3. output-to-rotated-buffer mapping places `(579,169)` in a different helper
     row/source coordinate than the current local strip interpretation.
- PNG-only candidate means cannot distinguish those three explanations,
  because all three can preserve the same broad strip while changing the typed
  numerator/denominator path.
- A local source edit before the typed witness returns would probably be a
  broad tuning change, not a binary-grounded fix.

## Acceptance Rule For Next Windows Return

Treat the return as answered for the angle-0 lane only if the same run includes
both `(494,169)` and `(579,169)` with all of:

- normalized parameters actually consumed by the render call
- output-to-A/B or output-to-rotated-buffer coordinate mapping
- helper-local source x/y
- actual touched destination x range on row `y=169`
- rowdriver/group membership at both witnesses
- denominator value at both witnesses
- `alpha_or_valid` or equivalent validity side-channel value at both witnesses
- accumulation numerator
- pre-writeback RGBA float/hex
- final stored RGBA bytes

Classify the return as `answered_partial` or `failed_partial` if it only proves
module load, only reports final PNG bytes, omits the helper-local destination
range, or collapses this angle-0 lane into the separate diagonal rotate lane.

## Next Action

Do not change `cli/OLMDirectionalBlur` or `mac/OLMDirectionalBlur` for this lane
until the helper-local witness above lands. Keep the active Windows request as
the priority send item.
