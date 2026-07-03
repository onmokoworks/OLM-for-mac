# OLMDistanceGradation case_0023 Witness Contract - 2026-07-01

This note narrows the live 16bpc Constant lane to the smallest witness set that
can still move implementation safely.

## Active lane

- request family:
  `olmdistancegradation_16bpc_constant_case0023_outside0_witness_20260630`
- case:
  `olmdistancegradation_extended__case_0023`
- mode:
  `In/Out=Both`, `Interpolation=Constant`, `Outside Threshold=0`

The remaining lane is not "DistanceGradation 16bpc in general". It is the
ownership rule for this one Constant helper family.

## What is already ruled out

- Broad Constant/no-blur compare tweaks are ruled out.
- Global plateau rewrites are ruled out.
- Final compose/writeback removal is ruled out.
- Viewer-space 8-bit spot numbers are not valid evidence for this lane.

The strongest rejection is the local `trunc_plateau_binary` probe:

- current residual: `73px`
- plateau probe residual: `182793px`

That probe slightly helps the targeted family but explodes the rest of the
frame, so it is not a promotable fix.

## Residual families that remain

The surviving `73px` split cleanly into two buckets:

1. edge bucket:
   - `65px`
   - `inside EDT = 1.0`
   - `outside EDT = 0.0`
   - representative witnesses:
     - `(1698,7)`
     - `(1699,7)`
     - `(1700,7)` as the adjacent outside-side contrast point
2. threshold bucket:
   - `8px`
   - `raw_inside` just above configured `Inside Threshold = 36`
   - representative witnesses:
     - `(414,393)` -> below threshold side
     - `(415,393)` -> just-above-threshold side
     - `(416,393)` -> further inside the plateau side

## Refreshed live Mac field facts

The 2026-07-01 single-case rerun reproduced the same live split:

- edge family:
  - `(1699,7)` -> `field_x=0`, `raw_inside=1`, `raw_outside=0`
  - `(1700,7)` -> `field_x=1`, `raw_inside=0`, `raw_outside=1`
- threshold family:
  - `(414,393)` -> `field_x=0`, `raw_inside=35.0142822`
  - `(415,393)` -> `field_x=1`, `raw_inside=36.0138855`
  - `(416,393)` -> `field_x=1`, `raw_inside=37.0135117`

This means the unresolved behavior is already decided in helper staging /
threshold ownership before final compose/writeback.

## Exact proof we still want

An actionable Windows runtime return for this lane should isolate one of these:

1. edge-family helper staging at the `inside=1.0 / outside=0.0` boundary, or
2. threshold-family helper staging at the `35.014 -> 36.013 -> 37.013` crossing

The useful typed facts are:

- the helper-stage field value before compose
- which side owns equality / plateau membership
- whether the Constant-only binary fork sees the pixel before or after that
  ownership decision

The currently shared Windows package is still edge-family-centric. See
`refs/conformance/olmdistancegradation_case0023_return_acceptance_20260701.md`
for how to classify a return that answers only `(1699,7)`-style witnesses but
not the threshold-family triplet around `(414..416,393)`.

## Implementation rule

Until one of those two witness families is typed from Windows:

- do not promote a global Constant helper rewrite
- do not retune final compose/writeback
- do not use broad PNG improvement as proof

The next code move must explain one of the two live buckets above.
