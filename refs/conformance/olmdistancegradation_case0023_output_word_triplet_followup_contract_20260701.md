# OLMDistanceGradation case_0023 Output-word Triplet Follow-up Contract - 2026-07-01

This follow-up accepts that the previous request already proved the
`414/415/416,393` crossing again. The missing fact is narrower: bind that
triplet at the actual helper/compose site using the output-word address or
compose refcon, not broad callback activity.

Target:

- request id:
  `olmdistancegradation_case0023_output_word_triplet_followup_20260701`
- case:
  `olmdistancegradation_extended__case_0023`
- witness triplet:
  `(414,393)`, `(415,393)`, `(416,393)`

Wanted proof:

1. derive triplet XY from the output-word address or compose refcon at
   `FUN_181170480`
2. stop only when one of the three witness pixels is bound at that hook
3. record typed values for:
   - raw inside/outside distances
   - helper-stage field value
   - exact threshold/equality/plateau decision
   - whether the Constant binary fork happens before or after that decision
   - value consumed by `FUN_181170480`
   - compose output before word store
   - final stored `RGBA16`

Actionable return must include:

- exact witness XY recovered from output-word address or compose refcon
- typed helper/compose values for the same pixel
- the exact failed bind/watchpoint reason if the output-word route still cannot be held

Forbidden until this lands:

- global Constant plateau retuning
- compose/writeback tuning from endpoints alone
- another broad callback log with no triplet-to-hook binding
