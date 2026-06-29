# OLMDirectionalBlur Pending Witness Proof

- Runtime package: `refs/runtime_trace_packages/olm_runtime_trace_directionalblur_residual_witness_20260629_helpercoverage.zip`

## Decision Boundary

Keep OLMDirectionalBlur blocked on typed witness proof only: the angle-0 strip still needs helper-local destination coverage or valid-alpha evidence, and the diagonal family still needs rotate/validity evidence. Broad PNG tuning and candidate promotion remain forbidden.

## Why Global Tuning Is Still Forbidden

- The best numeric candidates are still measurement scaffolds, not AEX-shaped implementations.
- The current runtime return is answered_partial but not actionable because it never captured typed per-pixel values after the module actually loaded.
- Local scatter-ownership audit shows the dominant angle-0 strip mask is unchanged by source-driven scatter, so broad scatter toggles are no longer the leading explanation.

## Angle-0 Lane

- Classification: `angle0-rgb-only-rowdriver-or-valid-alpha`
- Primary witness: `{'abs_delta_rgba': [164, 0, 0, 0], 'candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [164, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-164, 0, 0, 0], 'xy': [494, 169]}`
- Scan-order max witness: `{'abs_delta_rgba': [164, 0, 0, 0], 'candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [164, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-164, 0, 0, 0], 'xy': [465, 169]}`
- Current local readback: `{'witness_row_y': 169, 'full_segments': [[380, 579]], 'scatter_segments': [[380, 579]], 'identical_mask': True}`
- Helper-local static facts:
  - front helper call uses param_3 = 1
  - effective span is int(param_9 * param_11) with left-edge clipping
  - writes start at offset = 1
  - loop continues while offset < param_9
  - front helper writes only to destination columns strictly left of the current source x
- Endpoint constraint:
  `refs/conformance/olmdirectionalblur_angle0_endpoint_constraint_20260630.md`
  shows why the right strip endpoint is a real discriminator. The current local
  strip row ends at `x=579`, while the documented front helper writes strictly
  left of its source x and emits no center write. So a same-row front-helper
  explanation for endpoint `(579,169)` would require a contributing source
  `x >= 580`, which is outside the visible local strip. A useful Windows trace
  must therefore reveal either source-range evidence beyond the visible strip,
  a rotated-buffer/group-membership explanation, or another validity/alternate
  path.
- Required next proof: A helper-local source-to-destination range witness on the strip row, especially the right endpoint (579,169) plus companion witness (494,169), including actual touched destination x range, rowdriver/group membership, validity side-channel, accumulation, pre-writeback RGBA, and final bytes.

## Diagonal Lane

- Classification: `diagonal-rgb-alpha-rotate-validity`
- Primary witness: `{'abs_delta_rgba': [251, 0, 0, 0], 'candidate_rgba': [252, 0, 0, 255], 'reference_rgba': [1, 0, 0, 255], 'signed_delta_candidate_minus_reference': [251, 0, 0, 0], 'xy': [507, 367]}`
- Companion witnesses: `[{'abs_delta_rgba': [250, 0, 0, 0], 'candidate_rgba': [4, 0, 0, 255], 'reference_rgba': [254, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-250, 0, 0, 0], 'xy': [423, 187]}, {'abs_delta_rgba': [251, 0, 0, 0], 'candidate_rgba': [252, 0, 0, 255], 'reference_rgba': [1, 0, 0, 255], 'signed_delta_candidate_minus_reference': [251, 0, 0, 0], 'xy': [507, 367]}, {'abs_delta_rgba': [250, 0, 0, 0], 'candidate_rgba': [250, 0, 0, 255], 'reference_rgba': [0, 0, 0, 255], 'signed_delta_candidate_minus_reference': [250, 0, 0, 0], 'xy': [519, 363]}]`
- Current local readback: `{'scatter_vs_full_bbox': [0, 12, 580, 539], 'scatter_vs_full_max_abs': [5, 0, 0, 1]}`
- Required next proof: Typed rotate sampler source coordinates/order, border or validity decision, group-size or opacity gate, accumulation denominator, pre-writeback RGBA, and final bytes at the diagonal witnesses.

## Actionable Return Criteria

- The angle-0 return includes helper-local source x/y, param_1/param_3/param_9/param_11, clipped effective span, actual touched destination x range on row y=169, plus accumulation and final bytes.
- The diagonal return includes typed rotate/sampler/validity values at a real residual witness, not only final PNG bytes.
- The return keeps angle-0 and diagonal families separate instead of collapsing them into one generic rowdriver answer.

## Not Actionable

- It only repeats Software PNGs or broad candidate means without helper-local or per-pixel typed values.
- It promotes direct or rotated-front-strength because they score better numerically despite violating AEX-shaped facts.
- It treats source-driven scatter ownership as the main angle-0 fix even though the dominant strip mask is unchanged locally.

## Recommended Next Windows Probe

- Trace only the two classified OLMDirectionalBlur residual witnesses from `refs/reports/olmdirectionalblur_residual_clusters_20260622_022500/`. Do not recapture broad PNGs and do not tune from the candidate matrix. Use the 8bpc Software reference cases that feed the local `rotated-aex-full-choreo` probe. For angle-0/front-only `case_0001`, focus on the long-strip witness row `y=169`, especially `(494,169)` where Windows reference is `[164,0,0,255]` and the local candidate is `[0,0,0,255]`, plus the strip right endpoint `(579,169)` and, if convenient, the left endpoint `(380,169)`. Record parameter normalization (front/back strength, angle, Size Variation, Edge Fade, Sharp Tail, Noise), output-to-rotated-buffer coordinates for these pixels, rowdriver/group membership, validity/alpha side-channel values, and the helper-local destination coverage facts inside `FUN_1800038d0` / `FUN_1800013e0`: source x/y for the contributing helper call, `param_1`, `param_3`, `param_9` before scaling, `param_11`, `int(param_9 * param_11)` after scaling, any left-edge clip, the effective offset start/end, and the actual destination x range touched on the witness row. Also record accumulation numerator/denominator, pre-writeback floats/hex, and final stored RGBA for the same strip witness. For the diagonal rotate-path `case_0005`, focus on `(507,367)` where Windows reference is `[1,0,0,255]` and the local candidate is `[252,0,0,255]`. Record the same facts plus rotate sampler source coordinates/order, border/validity decision, group-size or opacity gating, and any normalize/divide step before final writeback. If the exact coordinate condition is too slow, first log the nearest high-diff row/diagonal component and return the exact condition that failed.
- If the full package is resent, force the angle-0 answer to include the right strip endpoint (579,169) in addition to (494,169), so row coverage and leftward-exclusive helper behavior can be checked directly.
- If the diagonal witness cannot be traced at the exact pixel first, return the nearest high-residual hit only if it still includes typed rotate/validity/pre-writeback values.
