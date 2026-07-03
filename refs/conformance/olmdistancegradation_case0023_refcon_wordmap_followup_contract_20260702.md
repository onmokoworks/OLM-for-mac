# OLMDistanceGradation case_0023 Refcon/Wordmap Follow-up Contract - 2026-07-02

This follow-up replaces the earlier output-word triplet retry after that return
came back `failed_partial` with a useful retry shape.

Target:

- request id:
  `olmdistancegradation_case0023_refcon_wordmap_followup_20260702`
- case:
  `olmdistancegradation_extended__case_0023`
- witnesses:
  `(414,393)`, `(415,393)`, `(416,393)`
- hook:
  `FUN_181170480`

Wanted proof:

1. dump the relevant refcon layout at `FUN_181170480`
2. recover xy/output-address mapping from `r8/r9/refcon`
3. set data breakpoints on the three `RGBA16` output word ranges
4. dump the same frame before store, with the triplet identity bound to the
   actual hook frame

Actionable return must include:

- recovered XY and output-word address for at least one of the triplet pixels
- typed values for:
  - helper-stage field value
  - exact threshold/equality/plateau decision
  - whether the Constant binary fork runs before or after that decision
  - value consumed by `FUN_181170480`
  - compose output RGBA before word store
  - final stored RGBA16
- the dumped refcon layout and pointer state if the bind still cannot be held

Forbidden until this lands:

- broad Constant-family reruns
- global plateau/equality rewrites from PNG-space tuning alone
- compose/writeback retuning without a triplet-bound consumed value
