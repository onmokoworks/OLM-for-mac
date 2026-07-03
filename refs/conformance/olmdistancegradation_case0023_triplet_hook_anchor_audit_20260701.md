# OLMDistanceGradation case_0023 Triplet Hook Anchor Audit

- Case: `olmdistancegradation_extended__case_0023`
- Triplet: `[[414, 393], [415, 393], [416, 393]]`
- Contract: `refs/conformance/olmdistancegradation_case0023_output_word_triplet_followup_contract_20260701.md`
- Decision: `triplet-bounded-compose-hook-still-missing`
- Reason: The local threshold triplet is already precise: `(414,393)` is below threshold with `field_x=0`, `(415,393)` is the first above-threshold point with `field_x=1`, and `(416,393)` stays on the same plateau side. So the missing Windows fact is no longer where the transition lives; it is the exact helper/compose hook that retains this XY identity and shows which typed value is consumed at the boundary.
- Why this anchor matters: This anchor removes the ambiguity around which boundary pixels matter. The remaining uncertainty is the typed ownership rule at the hook, not the existence of the red/blue endpoint flip.

## Same-Row Triplet

| Role | XY | field_x | raw_inside | raw_outside | inside-threshold | d_alpha | alpha |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `below_threshold_same_row` | `(414,393)` | `0.0` | `35.0142822` | `0.0` | `-0.9857178` | `1.0` | `1.0` |
| `first_above_threshold_same_row` | `(415,393)` | `1.0` | `36.0138855` | `0.0` | `0.0138855` | `1.0` | `1.0` |
| `deeper_plateau_same_row` | `(416,393)` | `1.0` | `37.0135117` | `0.0` | `1.0135117` | `1.0` | `1.0` |

## Vertical Context

| Role | XY | field_x | raw_inside | inside-threshold |
| --- | --- | ---: | ---: | ---: |
| `vertical_contrast_above` | `(415,392)` | `0.0` | `35.9026451` | `-0.0973549` |
| `vertical_contrast_below` | `(415,394)` | `1.0` | `36.0555115` | `0.0555115` |

## Windows Hook Ask

- Bind the triplet from the output-word address or compose refcon at the case-local helper/compose hook for `(414,393)`, `(415,393)`, `(416,393)`, and dump raw distances, helper-stage field value, Constant binary fork ordering, compose-consumed value, pre-store RGBA16, and final RGBA16.
- Wanted typed fields:
- raw inside/outside distances
- helper-stage field value
- threshold/equality/plateau decision
- Constant binary fork order
- FUN_181170480 consumed value
- compose output before word store
- final RGBA16

## Pending Windows Follow-up

- Request: `olmdistancegradation_case0023_output_word_triplet_followup_20260701`
- Status: `pending`
- Package: `refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_case0023_output_word_triplet_followup_20260701.zip`
- Acceptance: `refs/conformance/olmdistancegradation_case0023_output_word_triplet_return_acceptance_20260701.md`

## Reading

- The triplet itself is no longer the unknown.
- The first above-threshold point is already pinned locally at `(415,393)`.
- The remaining unknown is the typed ownership rule at the helper/compose hook that turns that local boundary into the final red/blue endpoint split.

