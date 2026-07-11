# OLMDirectionalBlur Lane State - 2026-07-03

- Decision: `freeze-rejected-global-toggles-keep-two-narrow-lanes`
- Structural base: `rotated-aex-full-choreo`
- Runtime status: `answered_partial`
- Runtime summary: The current package contains the exact Software reference renders for the two targeted cases and one prior live-attempt log, but no successful Windows per-pixel runtime trace. The prior live attempt failed before `OLMDirectionalBlur` resolved as a loaded module, so no rowdriver/rotate-path stage values were captured.
- Safe claim: DirectionalBlur remains split into two independent witness families: angle-0 rowdriver/valid-alpha and diagonal rotate/validity. Broad PNG tuning is still forbidden.
- Runtime package: `refs/runtime_trace_packages/olm_runtime_trace_requests_20260630_004241.zip`

## Angle-0 lane

- Classification: `angle0-rgb-only-rowdriver-or-valid-alpha`
- Primary witness: `{'abs_delta_rgba': [164, 0, 0, 0], 'candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [164, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-164, 0, 0, 0], 'xy': [494, 169]}`
- Required next proof: A helper-local source-to-destination range witness on the strip row, especially the right endpoint (579,169) plus companion witness (494,169), including actual touched destination x range, rowdriver/group membership, validity side-channel, accumulation, pre-writeback RGBA, and final bytes.
- Endpoint constraint: `{'rightmost_visible_strip_x': 579, 'required_min_source_x_for_same_row_front_helper': 580, 'same_row_segment_contains_that_source_x': False, 'implication': 'If the angle-0 endpoint pixel is produced by the documented front helper on the same row, the contributing source x must be strictly greater than the endpoint destination x because front writes only to the left. The current local strip row ends at x=579, so a same-row source inside that visible strip cannot explain the endpoint by itself.'}`

### Wanted fields

- helper-local source x/y
- param_1 / param_3 / param_9 / param_11
- effective span and touched destination x range
- rowdriver/group membership
- valid-alpha side-channel
- accumulation numerator/denominator
- pre-writeback RGBA and final bytes

## Diagonal lane

- Classification: `diagonal-rgb-alpha-rotate-validity`
- Primary witness: `{'abs_delta_rgba': [251, 0, 0, 0], 'candidate_rgba': [252, 0, 0, 255], 'reference_rgba': [1, 0, 0, 255], 'signed_delta_candidate_minus_reference': [251, 0, 0, 0], 'xy': [507, 367]}`
- Required next proof: Typed rotate sampler source coordinates/order, border or validity decision, group-size or opacity gate, accumulation denominator, pre-writeback RGBA, and final bytes at the diagonal witnesses.
- Companion witnesses: `[{'abs_delta_rgba': [250, 0, 0, 0], 'candidate_rgba': [4, 0, 0, 255], 'reference_rgba': [254, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-250, 0, 0, 0], 'xy': [423, 187]}, {'abs_delta_rgba': [251, 0, 0, 0], 'candidate_rgba': [252, 0, 0, 255], 'reference_rgba': [1, 0, 0, 255], 'signed_delta_candidate_minus_reference': [251, 0, 0, 0], 'xy': [507, 367]}, {'abs_delta_rgba': [250, 0, 0, 0], 'candidate_rgba': [250, 0, 0, 255], 'reference_rgba': [0, 0, 0, 255], 'signed_delta_candidate_minus_reference': [250, 0, 0, 0], 'xy': [519, 363]}]`

### Wanted fields

- rotate sampler source coordinates and order
- border/validity decision
- group-size or opacity gate
- accumulation denominator
- pre-writeback RGBA
- final bytes

## Allowed next actions

- Keep the current AEX-shaped base and patch only after typed Windows witness values land for one lane.
- Use angle-0 endpoint (579,169) plus interior witness (494,169) to prove helper coverage or alternate path membership.
- Use diagonal witnesses only for rotate sampler / validity / normalization proof, not for angle-0 tuning.

## Forbidden

- Do not retune prepass/scatter/direct/front-strength globally from PNG means.
- Do not merge angle-0 and diagonal residuals into one generic rowdriver theory.
- Do not treat the current helper-coverage return as actionable binary proof; it failed before module-local values were captured.

## Shared logging principles

- Stay on the AEX-shaped full choreography base while logging; direct and rotated-front-strength remain measurement baselines only.
- Capture typed values for A/B mapping, denominator, alpha_or_valid, numerator, pre-writeback, and final bytes in the same witness record.
- Treat angle-0 and diagonal as separate lanes even if one pass can log both.

## Inputs

- source_candidates_json: `refs/conformance/olmdirectionalblur_source_candidates_audit_20260701.json`
- hook_anchor_json: `refs/conformance/olmdirectionalblur_hook_anchor_audit_20260701.json`
- witness_prep_json: `refs/conformance/olmdirectionalblur_witness_logging_prep_20260702.json`