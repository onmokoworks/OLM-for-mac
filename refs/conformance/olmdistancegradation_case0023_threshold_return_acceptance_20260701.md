# OLMDistanceGradation case_0023 Threshold Return Acceptance - 2026-07-01

This note explains how to judge the next threshold-family-only Windows return
for `case_0023`.

## Current narrow package

- request id:
  `olmdistancegradation_case0023_threshold_family_followup_20260701`
- target witnesses:
  `(414,393)`, `(415,393)`, `(416,393)`

## `answered`

Classify the package as fully `answered` only if it returns actionable typed
threshold-family ownership facts:

- raw inside/outside distances at the triplet
- helper-stage field value before compose
- exact threshold/equality/plateau decision
- field value consumed by compose
- compose output before store
- final stored RGBA16

The point is to explain the `35.014 -> 36.013 -> 37.013` crossing, not merely
to reconfirm the final endpoints.

## `answered_partial`

Use `answered_partial` if the return is useful but still does not close the
threshold-family rule, for example:

- only one of the three threshold witnesses is typed
- final bytes are present but helper-stage ownership is missing
- a nearby witness is traced, but the decisive threshold crossing is not

## `trace-too-sparse` / `not isolated`

Use these if the return misses the proof boundary:

- PNGs only
- edge-family facts only
- broad Constant-branch narration without the threshold triplet values

## Forbidden promotion

Do not treat another edge-family answer as closing the live `case_0023` lane.

For this follow-up, success means the threshold-family crossing is typed.
