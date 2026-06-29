# OLMDirectionalBlur Angle-0 Endpoint Constraint

- Date: `2026-06-30`
- Case: `case_0001`
- Witness row: `y=169`
- Primary witness: `[494, 169]`

## Local Row Shape

- full segments: `[[380, 579]]`
- scatter segments: `[[380, 579]]`
- identical mask: `True`

## Static Helper Facts

- write direction: `front helper writes strictly left of the source x; back helper writes strictly right`
- front boundary: `front call clips span to x and starts at destination x-1`
- tail rule: `helper returns when effective span <= 1, so no zero-length or center write is emitted`

## Endpoint Reasoning

- rightmost visible strip x: `579`
- required same-row source x for front-helper-only explanation: `580`
- source exists inside visible strip: `False`
- implication: If the angle-0 endpoint pixel is produced by the documented front helper on the same row, the contributing source x must be strictly greater than the endpoint destination x because front writes only to the left. The current local strip row ends at x=579, so a same-row source inside that visible strip cannot explain the endpoint by itself.

## Decision

- `angle0-endpoint-needs-source-range-or-alternate-path-proof`

## Interpretation

- The local full/scatter masks are identical on row y=169 across x=380..579, so source-driven scatter ownership toggles do not change the existence of the strip itself.
- Static helper facts say the front helper writes strictly left of the source x and does not emit a center write.
- Therefore the right strip endpoint at x=579 is a high-value witness: a useful Windows trace must reveal either a contributing source x > 579, a rotated-buffer/group-membership explanation, or another validity/alpha side-channel or alternate path.
- This makes endpoint (579,169) complementary to interior witness (494,169): the endpoint tests row coverage/boundary logic, while the interior pixel tests accumulation/value logic inside the same strip family.
