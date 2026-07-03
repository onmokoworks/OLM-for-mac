# OLMDistanceGradation case_0023 Current-AEX Export Contract - 2026-07-02

Target:

- request id:
  `olmdistancegradation_case0023_current_aex_recapture_20260702`
- case:
  `olmdistancegradation_extended__case_0023_current_aex`
- render set:
  `SOFTWARE 16bpc`

Purpose:

- settle whether the remaining `73px` residual in current Mac AE output is
  still a live implementation mismatch, or partly a stale packaged-reference
  problem
- recapture the exact current installed Windows Software export for the same
  source and params used by the existing normalized 16bpc case_0023 lane

Witness pixels to inspect first:

- edge-family:
  - `(1698,7)`
  - `(1699,7)`
  - `(1700,7)`
- threshold-family controls:
  - `(414,393)`
  - `(415,393)`
  - `(416,393)`

Outcome A: current-AEX export matches the latest live Mac threshold triplet
and differs from the packaged expected PNG there

- classify the threshold-family slice as `reference-generation split`
- keep the edge-family lane separate until its current export values are known
- do not reopen helper/compose tuning from `(415,393)` alone

Outcome B: current-AEX export matches the packaged expected PNG at the
threshold-family witness

- the latest runtime-trace final triplet and the export class are not the same
  evidence object
- keep the lane in export/endgame classification until the discrepancy between
  trace and export class is explained

Outcome C: current-AEX export matches neither the packaged expected PNG nor the
current Mac single-case export

- record full provenance and treat the lane as current-export drift
- do not pretend the old packaged expected PNG is canonical for this slice

Forbidden until this lands:

- broad Constant helper rewrites from the old packaged expected PNG alone
- collapsing threshold-family and edge-family into one bug without a current
  Windows export
- treating the older packaged expected PNG as equivalent to current-AEX export
  without proof
