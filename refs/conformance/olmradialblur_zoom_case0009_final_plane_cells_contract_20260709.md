# OLMRadialBlur Zoom case_0009 Final-Plane Cell Witness Contract

## Purpose

This request is a narrow Windows runtime witness for `OLMRadialBlur` `case_0009`
from `refs/win_references/20260604_olm/OLMRadialBlur`.

The first return for this request was `failed_partial`: it provided package-local
candidate analysis, but no same-run Windows typed final-plane witness. Do not
answer a retry by restating local candidate cells, inferred cell offsets, or PNG
residual directions. The only useful proof is live Windows AEX data or the exact
hook/watchpoint failure artifact.

Do not tune from PNG residuals. The Mac-side probes show that the remaining
top-row alpha residual is not explained by final quantization alone. The next
proof needs the exact final polar-plane cells that Windows samples before the
output byte is written.

## Required Case

- Plug-in: `OLM RadialBlur`
- Case: `case_0009`
- Render lane: Windows AE Software render / current Windows AEX
- Input: `refs/win_references/20260604_olm/OLMRadialBlur/case_0009_before_effects.png`
- Expected/reference: `refs/win_references/20260604_olm/OLMRadialBlur/case_0009.png`

## Primary Witnesses

The Windows reference top row has alpha `254` only at:

- `(6, 0)`
- `(7, 0)`
- `(12, 0)`

The Mac candidate currently differs at these points. Capture each primary
pixel from the same run.

Special emphasis: local probes can already explain why `(6,0)` and `(12,0)`
may touch sub-one-alpha final-plane cells. `(7,0)` is the key anomaly: the
current local 4-cell set is all alpha `1.0`, while Windows still writes alpha
`254`. Prioritize the final inverse-sampler coordinate and four cell IDs for
`(7,0)`.

## Control / False-Positive Witnesses

Also capture nearby or candidate-false-positive controls:

- `(3, 0)`
- `(4, 0)`
- `(8, 0)`
- `(10, 0)`
- `(11, 0)`
- `(13, 0)`
- `(24, 0)`
- `(25, 0)`
- `(26, 0)`
- `(27, 0)`
- `(28, 0)`

These are important because the best local cell-offset candidate hits the three
primary pixels but also predicts these false positives. A successful answer
must explain why Windows includes or excludes them.

## Values To Capture Per Pixel

For each primary and control pixel, return:

- final output `x,y`
- Windows final RGBA8 byte
- pre-byte RGBA float immediately before final store, if observable
- final inverse-sampler coordinate used to read the polar/output plane
- radius/angle index or equivalent integer cell indices
- the four bilinear source cells used by the final sampler
- each cell's RGBA float/alpha before the final sample
- bilinear weights
- final-sample alpha sum before byte conversion
- final conversion rule observed, if separable (`truncate`, `+0.5`, SSE helper, other)
- exact hook/breakpoint/watchpoint address or failure reason

If source/prefill cells are available with little extra cost, include the
producer cell/source coordinate and alpha for any cell whose alpha is below
`1.0`.

## Local Evidence Included In Package

- `refs/conformance/olmradialblur_zoom_case0009_quantize_locus_20260709.md`
- `refs/conformance/olmradialblur_zoom_case0009_final_sample_float_sequence_20260709.md`
- `refs/conformance/olmradialblur_zoom_case0009_prefill_coordinate_probe_20260709.md`
- `refs/conformance/olmradialblur_zoom_case0009_cellset_candidate_20260709.md`
- `notes/IR_OLMRadialBlur.md`
- `notes/OLMRadialBlur_ASM_FACTS.md`

## Acceptance Rule

`answered` requires same-run typed final-plane cell facts for all three primary
pixels and at least four controls.

`answered_partial` is acceptable if at least one primary pixel has complete
final-plane cell facts and the return includes the exact reason the remaining
pixels could not be isolated.

Final PNG bytes alone, wrapper hit counts, or a restatement of local Mac
candidate values count as `failed_partial`.
