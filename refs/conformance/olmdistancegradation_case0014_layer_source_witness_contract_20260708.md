# OLMDistanceGradation case_0014 Layer-Source Witness Contract - 2026-07-08

Do not send this while another runtime package is active. This request is for
the remaining 16bpc Layer-source family after the depth-gated source-mask rule
closed `case_0023`.

## Request

- Request id: `olmdistancegradation_case0014_layer_source_witness_20260708`
- Effect: `OLM Distance Gradation`
- Case: `olmdistancegradation_extended__case_0014`
- Render set: Windows AE Software 16bpc
- Lane: `layer-no-bg-source-or-alpha-ownership`
- Primary witness: `(1652,2)`
- Secondary witness: `(461,6)`

## Why This Case

`case_0014` isolates the remaining broad Layer-source family better than
`case_0012` or `case_0013`: the primary witness has matching alpha in the
existing residual report, while RGB is still off by about 9.7k 16-bit codes.
That makes it a cleaner source-RGB/pre-store ownership proof than a mixed
RGB+alpha witness.

Existing witness from the older residual report:

- `(1652,2)` reference `[29399,29399,29399,43843]`
- `(1652,2)` candidate `[19713,19713,19713,43843]`
- delta `[-9686,-9686,-9686,0]`

## Required Capture

Use a live Windows stop in the final compose/writeback path, preferably
`FUN_181170480` if that is still the callback that owns this lane. For both
witness pixels, capture:

- consumed source-layer RGBA16
- source RGB before any unpremultiply
- source RGB after any unpremultiply
- source alpha used for ownership/mask
- field pixel / field channels presented to compose
- final `X`, `d_alpha`, and `out_a`
- output RGBA float immediately before `CVTTSS2SI`
- final stored RGBA16
- exported RGBA16/PNG bytes if observable in the same run

## Acceptance

`answered`:

- both witness pixels hit the live Windows callback and have typed same-run
  values covering source RGBA16, field/compose inputs, pre-store RGBA float,
  and final stored RGBA16.

`answered_partial`:

- one witness pixel is complete, or both pixels have source/field records but
  one downstream value is missing.

`failed_partial`:

- the callback or stage is reached, but neither witness gets enough typed
  values to decide the source-RGB/pre-store rule.

`failed`:

- final PNG bytes only, broad hit counts, surrogate cases, or a restatement of
  the existing residual report.

## Decision Rule

- If `straight_source_rgb * out_a` matches Windows pre-store/final RGB within
  `<=1` 16-bit code at both pixels, keep the Layer-source ownership rule and
  look downstream/local for the remaining Mac difference.
- If it does not match, or Windows consumes a different source form before
  compose, classify `case_0014` as a remaining Layer-source rule gap.

## Forbidden

- Do not use this request to retune field topology, depth gating, or the
  `case_0024..0027` export-quantization family.
- Do not use CLI output as Windows truth.
- Do not change Mac implementation from `answered_partial` unless the missing
  value is irrelevant to the proven rule.
