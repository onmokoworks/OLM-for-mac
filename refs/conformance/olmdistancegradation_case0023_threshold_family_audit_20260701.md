# OLMDistanceGradation case_0023 Threshold-Family Audit

- Case: `olmdistancegradation_extended__case_0023`
- Mode: `Interpolation=Constant`, `In/Out=Both`, `Outside Threshold=0`
- Decision: `threshold-family-historical-bounded-context`
- Reason: The current residual is only 73px and already splits into two helper-stage buckets, including an 8px threshold-family crossing at raw_inside 35.014 -> 36.013 -> 37.013. Local field debug proves the field_x flip happens before compose, while the broad trunc_plateau_binary probe explodes the frame to 182793px. This lane is now historical bounded context: it explains why broad Constant rewrites stay forbidden, while the live Windows ask has moved to the narrower output-word / compose-refcon triplet witness.
- Forbidden action: Do not promote a global Constant plateau/equality tweak or compose/writeback retune from the current local evidence alone.
- Next Windows requirement: Bind the `414/415/416,393` triplet from the output-word address or compose refcon at `FUN_181170480`; do not accept another broad callback stop with no retained XY.

## Residual Split

- Total residual px: `73`
- Endpoint pairs: `{'65535,0,0,65535 -> 7195,0,61165,65535': 8, '7195,0,61165,65535 -> 65535,0,0,65535': 65}`
- Edge bucket: `inside=1.0` / `count=65` / `outside=[0.0]`
- Threshold bucket: `inside=36.013885498046875` / `count=8` / `outside=[0.0]`

## Threshold Triplet

| Role | XY | field_x | raw_inside | inside-threshold | raw_outside | d_alpha |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `below_threshold_same_row` | `(414,393)` | `0.0` | `35.0142822` | `-0.9857178` | `0.0` | `1.0` |
| `first_above_threshold_same_row` | `(415,393)` | `1.0` | `36.0138855` | `0.0138855` | `0.0` | `1.0` |
| `deeper_plateau_same_row` | `(416,393)` | `1.0` | `37.0135117` | `1.0135117` | `0.0` | `1.0` |
| `vertical_contrast_above` | `(415,392)` | `0.0` | `35.9026451` | `-0.0973549` | `0.0` | `1.0` |
| `vertical_contrast_below` | `(415,394)` | `1.0` | `36.0555115` | `0.0555115` | `0.0` | `1.0` |

## Plateau Probe Rejection

- Current residual px: `73`
- Plateau residual px: `182793`
- Edge bucket delta: `14922`
- Threshold bucket current -> plateau: `8 -> 8`
- Threshold bucket delta: `0`
- Threshold bucket invariant under plateau probe: `True`

## Pending Windows Follow-up

- Request: `olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702`
- Status: `pending`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_refcon_stack_wordmap_followup_20260702.zip`
- Acceptance: `refs/conformance/olmdistancegradation_case0023_refcon_stack_wordmap_return_acceptance_20260702.md`
- Stop condition: Return enough typed values to explain the `case_0023` triplet crossing with XY bound from recovered output-word/refcon/stack mapping at `FUN_181170480`. If even that stop cannot be isolated, return the precise failed bind/watchpoint reason plus the exact address/condition and the dumped `r8/r9/[rsp+0x28]` layout and pointer state needed for the next retry.

## Reading

- The threshold-family lane is already bounded locally: `(414,393)` stays below threshold, `(415,393)` is the first above-threshold side, and `(416,393)` is deeper into the same plateau side.
- The broad plateau rewrite is explicitly non-promotable because it turns a 73px lane into a 182793px frame-wide regression.
- This audit is historical bounded context only; the live Windows requirement is now the narrower output-word / compose-refcon triplet witness.

