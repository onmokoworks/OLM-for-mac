# OLMRadialBlur Decision Matrix

- Decision: `blocked-needs-narrow-proof`
- Recommended action: Do not promote broad RadialBlur toggles from PNG matrices. Zoom is alpha-normalization/sampler-side; tiny Rotation needs sampler/validity proof; Inner needs typed per-cell helper evidence.

## Zoom

- Decision: `guarded-alpha-normalization`
- Case/XY: `case_0009` `[6, 0]`
- Local floor minus Windows u8: `[0, 0, 0, 1]`
- Next evidence: Zoom polar alpha/sample accumulation; not final byte packing.

## Tiny Rotation

- Decision: `blocked-sampler-validity`
- Classification: `inverse-sampler / validity-side unresolved; not explained by a simple final byte conversion tie`
- Final u8: `[255, 255, 255, 255]`
- Closest sampler float: `[-0.004081939347088337, -0.004081939347088337, -0.004081939347088337, 1.0]`
- Next evidence: Exact inverse-sampler validity/border and pre-writeback path for the high-max top-border witness.

## Inner

- Decision: `blocked-no-global-toggle`
- Best by mean sum: `loop-minus-one`
- Exact candidates: `[]`
- Next evidence: Typed FUN_180001c90 per-cell witness for one low-span cell and one Quality/strong cell.

| Candidate | Mean sum | Max max | Improved | Worsened | Exact |
| --- | ---: | ---: | ---: | ---: | ---: |
| `loop-minus-one` | 63.793179 | 255 | 7 | 3 | 0 |
| `circular-wrap` | 64.221060 | 255 | 4 | 6 | 0 |
| `grid-aex-float` | 64.313231 | 255 | 6 | 4 | 0 |
| `dynamic-offset-aex-row` | 64.313402 | 255 | 2 | 0 | 0 |
