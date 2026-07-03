# OLMRadialBlur Decision Matrix

- Decision: `blocked-needs-narrow-proof`
- Recommended action: Do not promote broad RadialBlur toggles from PNG matrices. Zoom is alpha-normalization/caller-collapse-side; tiny Rotation needs upstream polar RGB / substitute-path proof; Inner needs typed per-cell helper evidence.

## Zoom

- Decision: `guarded-alpha-normalization`
- Case/XY: `case_0009` `[6, 0]`
- Local floor minus Windows u8: `[0, 0, 0, 1]`
- 2026-07-01 row probe: final alpha stays near-opaque across `x=2..10`, while
  the current local validity proxy collapses far earlier (`max gap=208` at
  `x=8`).
- 2026-07-01 propagated-validity probe: a same-kernel propagated validity plane
  leaves the current Zoom diff unchanged (`max=1 mean=0.0046`).
- Next evidence: Zoom caller-collapse alpha/sample accumulation into `+0xe`;
  not final byte packing and not direct sampling of the current validity plane.

## Tiny Rotation

- Decision: `blocked-upstream-rgb-substitute`
- Classification: `inverse-sampler return is still near-black, so the live blocker is upstream polar RGB / substitute-path ownership rather than a simple validity-side or final-byte tie`
- Final u8: `[255, 255, 255, 255]`
- Closest sampler float: `[-0.004081939347088337, -0.004081939347088337, -0.004081939347088337, 1.0]`
- 2026-07-01 row probe: validity alpha is already fully live across
  `x=1610..1618`; the witness stays black only at `(1614,6)`.
- 2026-07-01 propagated-validity probe: final stats stay effectively unchanged
  (`max=255 mean=0.0103`).
- Next evidence: Exact upstream polar RGB / substitute-path population and then
  the pre-writeback path for the high-max top-border witness.

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

### Inner Witness Plan

- Decision: `typed-inner-cell-witnesses-only`
- Recommended action: Do not promote global Inner toggles. If Windows is needed, trace one representative low-span cell and one Quality/strong cell; add Edge Fade prepass only if the first two do not explain the split.

| Family | Representative | Best candidate | Baseline mean | Best mean | Required proof |
| --- | --- | --- | ---: | ---: | --- |
| `low-span` | `rb_inner_only_strength_large` | `circular-wrap` | 0.189705 | 0.124590 | Typed FUN_180001c90 values for one low-span cell: resolved span, table index, row/underflow target, source/destination polar cell, and accumulated RGBA/denom. |
| `quality-strong` | `rb_inner_quality_1` | `loop-minus-one` | 15.253006 | 14.856614 | Typed FUN_180001c90 values for one Quality/strong cell: resolved span, loop bound, table divisor, gaussian weight, source row, and post-scatter accumulation. |
| `edge-prepass` | `rb_inner_edgefade_only` | `table-span-minus-one` | 3.957052 | 3.920890 | Prepass alpha/factor plane and scatter denominator values for one Edge Fade cell before changing table bounds. |

### Inner Cell Witness Return

- Status: `answered_partial`
- Failure classification: `partial_trace_after_effective_span`
- Summary: Captured first-hit inner-helper callsite and post-effective-span state for the requested low-span, quality-strong, and edge-prepass representatives. The exact per-cell scatter body/table-step trace was interrupted by second-chance access violations after the effective span was recorded; therefore this return provides typed closest local values rather than a full accumulation/denominator/writeback witness.

| Family | Case | Base span hex | Effective span | Span gate | Fault site | Fault instruction |
| --- | --- | --- | ---: | ---: | --- | --- |
| `low-span` | `rb_inner_only_strength_large` | `000001dd` | 477 | 1.000000000 | `OLMRadialBlur+0x222d` | `mulss xmm2,dword ptr [r13+rcx*4+1D528h]` |
| `quality-strong` | `rb_inner_quality_1` | `00000033` | 51 | 0.010600490 | `OLMRadialBlur+0x2194` | `addss xmm0,dword ptr [r8]` |
| `edge-prepass` | `rb_inner_edgefade_only` | `000000ff` | 255 | 0.501960874 | `OLMRadialBlur+0x222d` | `mulss xmm2,dword ptr [r13+rcx*4+1D528h]` |

Not isolated:
- specific representative residual cell chosen by output pixel
- full loop bound through all scatter iterations
- source/destination polar row/column for every scatter write
- accumulated RGBA numerator and denominator
- post-scatter value consumed by final writeback
