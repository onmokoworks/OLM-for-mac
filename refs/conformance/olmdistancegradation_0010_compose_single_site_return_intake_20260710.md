# OLMDistanceGradation Single-Site Return Intake

Date: 2026-07-10

Request: `olmdistancegradation_0010_compose_single_site_followup_20260710`

Classification: `answered_partial`

## Accepted Facts

- Windows ran separate field and source processes for case_0010 `(6,40)`.
- Both reached `DistanceGradation+0x1170480` and reconstructed the output base
  and exact target output address using `rowbytes=0x3c00`, pixel size `8`.
- Neither run recorded `EXACT_SITE_HIT`; no field/source words were captured.

## Exact Failure

Both CDB consoles stop immediately after the entry witness on first-chance
`Break instruction exception - code 80000003`, then execute the script's end
commands. The selected downstream breakpoint is armed and resolved, but the
debugger never continues far enough to evaluate it.

This is a debugger-control failure, not evidence that the field/source sites or
`RDI` gate are wrong. The successor package adds `sxi 80000003` and preserves
the same one-target/one-site design.

No Mac source change is authorized by this return.
