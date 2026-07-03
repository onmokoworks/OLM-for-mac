# OLMDistanceGradation case_0023 Triplet XY Compose Follow-up Contract - 2026-07-01

This follow-up narrows the threshold-family triplet witness one step further.
The previous return already confirmed the endpoint flip at
`(414,393)`, `(415,393)`, `(416,393)`. The missing fact is no longer the flip
itself; it is the case-local helper/compose hook with the triplet XY identity
still attached.

Target:

- request id:
  `olmdistancegradation_case0023_triplet_xy_compose_hook_followup_20260701`
- case:
  `olmdistancegradation_extended__case_0023`
- witness triplet:
  `(414,393)`, `(415,393)`, `(416,393)`

Wanted proof:

1. keep the triplet XY identity alive at the actual helper/compose hook
2. record typed values for:
   - raw inside/outside distances
   - helper-stage field value
   - exact threshold/equality/plateau decision
   - whether the Constant binary fork happens before or after that decision
   - value consumed by `FUN_181170480`
   - compose output before word store
   - final stored `RGBA16`

Actionable return must include:

- exact case and XY at the hook point itself
- typed values, not only final endpoint colors
- exact failed hook/callsite reason if the case-local stop still cannot be held

Forbidden until this lands:

- global Constant plateau/equality retuning
- compose/writeback tuning from final endpoints alone
- broad callback logs without retained triplet XY identity
