# OLMRadialBlur Pending Narrow Proof

## Decision Boundary

Keep OLMRadialBlur blocked on narrow binary proof only: Zoom still needs upstream alpha-normalization evidence, tiny Rotation still needs exact inverse-sampler/validity evidence, and Inner still needs one typed helper-to-output witness that survives past effective span into real accumulation/writeback.

## Why Global Tuning Is Still Forbidden

- Zoom already has Windows sampler/pre-output floats that truncate to the exact Windows bytes, so final byte packing is not the live issue.
- tiny Rotation already rejects the closest traced inverse-sampler sample as the final explanation because it truncates to black while the exact Windows output is white.
- Inner already has binary-grounded helper facts and candidate matrices, but no global loop/wrap/table toggle is exact and the best candidates split by family.

## Narrow Lanes

### zoom

- Classification: `pre-output alpha-normalization / sampler-side residual; not a later byte-writer mismatch`
- Case: `case_0009`
- Witness: `{'x': 6, 'y': 0, 'reference_rgba': [20, 3, 3, 254], 'mac_candidate_rgba': [20, 3, 3, 255], 'signed_delta_candidate_minus_reference': [0, 0, 0, 1]}`
- Windows pre-writeback RGBA float: `[0.08224078267812729, 0.014130095019936562, 0.014130095019936562, 0.9999999403953552]`
- Windows final RGBA u8: `[20, 3, 3, 254]`
- Caller collapse boundary: `{'sampler_helpers': {'nonrepeat_rgba': 'FUN_180001270', 'repeat_rgba': 'FUN_180001520'}, 'preserved_validity_plane': '+0xf252', 'normalized_accum_rgba_plane': '+0xf250', 'final_polar_rgba_plane': '+0xe'}`
- Required next proof: Polar alpha/sample accumulation before sampler return, including the denominator or substitute alpha state that explains Windows alpha 0.99999994 versus local 1.0, plus the caller-side collapse from preserved validity/+0xf252 into final +0xe alpha.
- 2026-07-01 local row-probe strengthening: across witness row `x=2..10`, final
  inverse-sampled alpha stays near-opaque while the current local
  preserved-validity proxy collapses rapidly (`max alpha_u8 - validity_alpha_u8
  gap = 208` at `x=8`). Therefore the next proof is narrower than direct
  bilinear sampling of the current validity plane.

### tiny_rotation

- Classification: `inverse-sampler / validity-side unresolved; not explained by a simple final byte conversion tie`
- Case: `case_0010`
- Witness: `{'x': 1614, 'y': 6, 'reference_rgba': [255, 255, 255, 255], 'mac_candidate_rgba': [0, 0, 0, 255], 'signed_delta_candidate_minus_reference': [-255, -255, -255, 0]}`
- Closest traced sampler RGBA float: `[-0.004081939347088337, -0.004081939347088337, -0.004081939347088337, 1.0]`
- Windows final RGBA u8: `[255, 255, 255, 255]`
- Caller collapse boundary: `{'preserved_validity_plane': '+0xf252', 'normalized_accum_rgba_plane': '+0xf250', 'final_polar_rgba_plane': '+0xe', 'final_inverse_sampler': 'FUN_180009d80'}`
- Required next proof: Exact inverse-sampler validity/border or substitute late path for the top-border high-max witness, plus the caller-side collapse values: preserved validity/+0xf252, accumulated +0xf250 RGBA, normalized +0xe RGBA, and then the final output if the sampler sample is bypassed.
- 2026-07-01 local row-probe strengthening: across witness row `x=1610..1618`,
  validity alpha is already fully live everywhere (`gap = 0` at all sampled
  points), while the center witness alone drops from white to black. So the
  remaining tiny Rotation proof should now focus on upstream polar RGB /
  substitute-path population rather than a validity-only alpha collapse.

### inner

- Classification: `partial_trace_after_effective_span`
- Typed effective spans: `[{'case_id': 'rb_inner_only_strength_large', 'family': 'low-span', 'effective_span': 477, 'span_gate_float': 1.0, 'fault_site': 'OLMRadialBlur+0x222d'}, {'case_id': 'rb_inner_quality_1', 'family': 'quality-strong', 'effective_span': 51, 'span_gate_float': 0.010600490495562553, 'fault_site': 'OLMRadialBlur+0x2194'}, {'case_id': 'rb_inner_edgefade_only', 'family': 'edge-prepass', 'effective_span': 255, 'span_gate_float': 0.5019608736038208, 'fault_site': 'OLMRadialBlur+0x222d'}]`
- Required next proof: One typed helper-to-output witness that stays on the same helper instance beyond effective span: resolved span, table step/index, source and destination polar cell, accumulated RGBA numerator/denominator, and pre-writeback RGBA.

## Actionable Return Criteria

- Zoom returns the actual polar alpha/sample accumulation state at case_0009 witness (6,0), including any preserved validity/+0xf252 to +0xe alpha collapse, not just the already-known final bytes or sampler return.
- tiny Rotation returns the exact validity/border branch or substitute path for witness (1614,6), plus +0xf252, +0xf250 RGBA, normalized +0xe RGBA, and the final output that becomes the white pixel.
- Inner binds one representative output witness to one helper instance and records values after +0x1d18 all the way through accumulation/denominator/writeback.

## Not Actionable

- It only repeats final PNG bytes or the already-grounded closest sampler return for Zoom/tiny Rotation without the caller-side +0xf252/+0xf250/+0xe collapse state.
- It proposes broad loop-minus-one, circular-wrap, table-span-minus-one, or final-byte tweaks without witness values that survive to writeback.
- Inner tracing stops again immediately after effective span without isolating the actual destination cell and accumulated numerator/denominator.

## Recommended Next Windows Probe

- Zoom case_0009 at (6,0): capture polar/sample accumulation alpha, normalization denominator or equivalent, sampler return RGBA, preserved validity/+0xf252, accumulated +0xf250 RGBA, normalized +0xe RGBA, pre-writeback RGBA, and final bytes in one chain.
- tiny Rotation case_0010 at (1614,6): capture inverse-sampler input XY, validity/border branch decision, any fallback/substitute path, preserved validity/+0xf252, accumulated +0xf250 RGBA, normalized +0xe RGBA, pre-writeback RGBA, and final bytes in one chain.
- Inner: choose one low-span witness and one quality-strong witness, but bind each to a concrete output pixel so the trace can follow the same helper instance into destination accumulation and writeback.
