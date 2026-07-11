# OLMDistanceGradation 0010 Break-Ignore Return Intake

Date: 2026-07-10

Request:
`olmdistancegradation_0010_compose_single_site_break_ignore_retry_20260710`

Return:
`20260710_092500__olmdistancegradation_0010_compose_single_site_break_ignore_retry_partial_windows.zip`

Classification: `answered_partial`

## FACT

- Both runs used a launcher containing `sxi 80000003`.
- The source run loaded `DistanceGradation.aex`, armed both software `bp`
  stops, and hit the entry stop at callback coordinates `(0,90)`.
- That live stop produced `output_base=0x000001a10d8b0100` and the requested
  `(6,40)` address `0x000001a10d9a0130`.
- The source run never emitted `EXACT_SITE_HIT`; it entered project-close
  activity after the entry witness. The AE runner separately reported
  `PNG was not written`.
- The field run lost its runnable debuggee before retaining an entry or
  downstream typed witness.
- No RCX field words, RDX source words, XMM values, or PF16 writer words were
  returned. This is not compose-math evidence.

## INFERENCE

- The live entry hit proves that `sxi 80000003` did not suppress every
  debugger-set software breakpoint in this run. Replacing the same stops with
  hardware breakpoints is therefore not the primary next action.
- The first callback observed at `y=90` is evidence that target `(6,40)` may
  lie outside the rendered callback tile. That explains a missing exact-site
  hit more directly than a breakpoint-type hypothesis, but the complete tile
  extent was not logged and remains unproven.

## Next Action

Run only the already-grounded second residual target `(901,394)`, source site
`DistanceGradation+0x11705f1`, with the same live output-base relation. This
target is below the observed `y=90` tile start and avoids another broad or
multi-site request. Retain entry coordinates, exact `RDI`/target comparison,
typed `RDX` words, and the AE runner result even if PNG export fails.

