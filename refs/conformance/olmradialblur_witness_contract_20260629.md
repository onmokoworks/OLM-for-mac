# OLMRadialBlur Witness Contract

- Decision: `blocked-narrow-proof-only`
- Next step: Read/trace only the listed narrow proof points; no broad PNG tuning or global helper toggles.

## Keep

- Do not change final byte packing for Zoom case_0009; Windows floats truncate to the Windows bytes.
- Do not treat the closest tiny-Rotation sampler return as the final pre-writeback value.
- Do not promote loop-minus-one, table-span-minus-one, circular-wrap, or grid-aex-float globally.
- Keep static FUN_180001c90 facts: effective span truncation, table divisor by R14D, inner tail < R14D, underflow to next radius row.

## Zoom

- Case/XY: `case_0009` `[6, 0]`
- Classification: `pre-output alpha-normalization / sampler-side residual; not a later byte-writer mismatch`
- Local float: `[0.08224090933799744, 0.014130176045000553, 0.014130176045000553, 1.0]`
- Windows float: `[0.08224078267812729, 0.014130095019936562, 0.014130095019936562, 0.9999999403953552]`
- Local floor minus Windows u8: `[0, 0, 0, 1]`
- Required proof: Zoom polar alpha/sample accumulation before sampler return; final byte conversion is already ruled out.

## Tiny Rotation

- Case/XY: `case_0010` `{'mac_candidate_rgba': [0, 0, 0, 255], 'reference_rgba': [255, 255, 255, 255], 'signed_delta_candidate_minus_reference': [-255, -255, -255, 0], 'x': 1614, 'y': 6}`
- Classification: `inverse-sampler / validity-side unresolved; not explained by a simple final byte conversion tie`
- Closest sampler float: `[-0.004081939347088337, -0.004081939347088337, -0.004081939347088337, 1.0]`
- Closest sampler floor u8: `[0, 0, 0, 255]`
- Windows final u8: `[255, 255, 255, 255]`
- Required proof: Exact inverse-sampler validity/border branch or substitute pre-writeback path for the top-border high-max witness.

## Inner

- Classification: `blocked-no-global-toggle`
- Best by mean sum: `loop-minus-one`
- Exact candidates: `[]`
- Required proof: Typed FUN_180001c90 per-cell values for a low-span cell and a Quality/strong cell before changing loop/table/wrap behavior.

| Candidate | Mean sum | Max max | Improved | Worsened | Exact |
| --- | ---: | ---: | ---: | ---: | ---: |
| `loop-minus-one` | 63.793179 | 255 | 7 | 3 | 0 |
| `circular-wrap` | 64.221060 | 255 | 4 | 6 | 0 |
| `grid-aex-float` | 64.313231 | 255 | 6 | 4 | 0 |
| `dynamic-offset-aex-row` | 64.313402 | 255 | 2 | 0 | 0 |

## Static Scatter Facts

- effective_span: `R14D = trunc(float(resolved_distance) * span_gate)`
- table_step: `step = int(30000 / R14D)`
- inner_tail: `offset starts at 1 and continues while offset < R14D`
- underflow: `when angular index underflows, target advances to the next radius row tail`
