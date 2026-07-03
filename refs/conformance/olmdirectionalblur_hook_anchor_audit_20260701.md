# OLMDirectionalBlur Hook Anchor Audit

- Contract: `refs/reports/olmdirectionalblur_witness_contract_20260624/witness_contract.md`
- Runtime package: `refs/runtime_trace_packages/olm_runtime_trace_requests_20260630_004241.zip`
- Decision: `two-independent-hook-anchors-still-missing-typed-runtime-values`
- Reason: DirectionalBlur no longer lacks witness coordinates; it lacks typed runtime values at two already separated families. Angle-0 is the long RGB-only strip on row `y=169`, where alpha already matches and the key unresolved question is helper-local destination coverage or a validity-side channel. Diagonal is a separate rotate/validity family with signed red errors in both directions.
- Why this anchor matters: This anchor removes the remaining ambiguity about which DirectionalBlur pixels matter. The next Windows value should prove one of two bounded theories, not reopen broad candidate fitting.

## Angle-0 Anchor

- Classification: `angle0-rgb-only-rowdriver-or-valid-alpha`
- Primary witness: `{'abs_delta_rgba': [164, 0, 0, 0], 'candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [164, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-164, 0, 0, 0], 'xy': [494, 169]}`
- Strip endpoint witness: `{'xy': [579, 169]}`
- Scan-order max witness: `{'abs_delta_rgba': [164, 0, 0, 0], 'candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [164, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-164, 0, 0, 0], 'xy': [465, 169]}`
- full segments: `[[380, 579]]`
- scatter segments: `[[380, 579]]`
- identical mask under scatter toggle: `True`
- Endpoint constraint: {'rightmost_visible_strip_x': 579, 'required_min_source_x_for_same_row_front_helper': 580, 'same_row_segment_contains_that_source_x': False, 'implication': 'If the angle-0 endpoint pixel is produced by the documented front helper on the same row, the contributing source x must be strictly greater than the endpoint destination x because front writes only to the left. The current local strip row ends at x=579, so a same-row source inside that visible strip cannot explain the endpoint by itself.'}
- Helper-local static facts:
- front helper call uses param_3 = 1
- effective span is int(param_9 * param_11) with left-edge clipping
- writes start at offset = 1
- loop continues while offset < param_9
- front helper writes only to destination columns strictly left of the current source x

Wanted angle-0 fields:
- helper-local source x/y
- param_1 / param_3 / param_9 / param_11
- effective span and touched destination x range
- rowdriver/group membership
- valid-alpha side-channel
- accumulation numerator/denominator
- pre-writeback RGBA and final bytes

## Diagonal Anchor

- Classification: `diagonal-rgb-alpha-rotate-validity`
- Primary witness: `{'abs_delta_rgba': [251, 0, 0, 0], 'candidate_rgba': [252, 0, 0, 255], 'reference_rgba': [1, 0, 0, 255], 'signed_delta_candidate_minus_reference': [251, 0, 0, 0], 'xy': [507, 367]}`
- Companion witnesses: `[{'abs_delta_rgba': [250, 0, 0, 0], 'candidate_rgba': [4, 0, 0, 255], 'reference_rgba': [254, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-250, 0, 0, 0], 'xy': [423, 187]}, {'abs_delta_rgba': [251, 0, 0, 0], 'candidate_rgba': [252, 0, 0, 255], 'reference_rgba': [1, 0, 0, 255], 'signed_delta_candidate_minus_reference': [251, 0, 0, 0], 'xy': [507, 367]}, {'abs_delta_rgba': [250, 0, 0, 0], 'candidate_rgba': [250, 0, 0, 255], 'reference_rgba': [0, 0, 0, 255], 'signed_delta_candidate_minus_reference': [250, 0, 0, 0], 'xy': [519, 363]}]`
- scatter_vs_full_bbox: `[0, 12, 580, 539]`
- scatter_vs_full_max_abs: `[5, 0, 0, 1]`

Wanted diagonal fields:
- rotate sampler source coordinates and order
- border/validity decision
- group-size or opacity gate
- accumulation denominator
- pre-writeback RGBA
- final bytes

## Windows Hook Ask

- Keep the angle-0 strip witnesses `(494,169)` and `(579,169)` separate from the diagonal witness `(507,367)`, and return helper-local / rowdriver-group / valid-alpha coverage facts for the former plus typed rotate-sampler / border-validity / group-size-normalization facts for the latter.

## Reading

- Angle-0 and diagonal are still independent lanes.
- Angle-0 is already bounded to helper-local destination coverage / rowdriver-group / valid-alpha facts on row 169.
- Diagonal is already bounded to rotate-sampler / border-validity / group-size-normalization facts at the high-residual rotate path.
- The next useful Windows return should prove one of those bounded theories, not repeat broad PNGs or module-load failures.

