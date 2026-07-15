# OLMDistanceGradation 8bpc Coordinate Liveness Census Return

Date: 2026-07-15

## Verdict

`answered / observation-only`

The return satisfies the bounded coordinate-liveness census request. It does
not claim AE exactness and does not close the older typed-boundary request at
`(397,281)`. Instead, it proves that the PF8 callback is live over a wide ROI
while that coordinate and its radius-2 neighborhood are not visited by this
hook in any of the three requested cases.

## Facts

- Return archive SHA-256:
  `f69f1635d8cbc19221fbb1a69c7707b4a33ccd5f901c82b39dbd09b234476771`.
- All cases use AE `25.2x131`, Software rendering, 8bpc, and AEX SHA-256
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- The shared run ID is
  `dg8census-e4386a6ed631424492e28db41ba61523`; each case uses a fresh AE
  process as required.
- PF32 callback count is zero in every case.
- PF8 census results:

| Case | AE PID | PF8 hits | x range | y range | `(397,281)` radius-2 hits |
| --- | ---: | ---: | --- | --- | ---: |
| `case_0001` | `39392` | `24714` | `0..1919` | `0..1073` | `0` |
| `case_0015` | `55216` | `9310` | `0..1919` | `0..1079` | `0` |
| `case_0029` | `51532` | `3439` | `0..1919` | `0..1075` | `0` |

- The rendered output hashes match the packaged Windows reference images for
  all three cases.
- Confirmed live common anchors include `(0,0)`, `(0,45)`, `(0,90)`, and
  `(0,135)`. Confirmed live interior samples include `case_0001 (183,181)`,
  `case_0015 (232,270)`, and `case_0029 (1185,180)`.
- The archive retains the per-case CDB traces, AE logs/results, ready markers,
  rendered PNGs, and the combined CDB trace.

## Mac Residual Intersection

A fresh Mac AE `26.3x87` run at explicit 8bpc, working space `None`, and linear
blending off reproduced the current-binary metrics and artifact hashes recorded
by the earlier Mac typed-boundary report:

| Case | Mac PNG SHA-256 | max diff | differing pixels | Census-confirmed live residual |
| --- | --- | ---: | ---: | --- |
| `case_0001` | `4e38e5fd4d4be8c8cee366a4ffebe7499832635ffed3f426f13a08417ce66185` | `2` | `195682` | None among retained coordinates; first residual is `(17,0)`, adjacent to live anchor `(0,0)` |
| `case_0015` | `393f60193b5536d9c79a17fa23964cfdaceb91b54c0f262463ff3b2eb262c8fb` | `64` | `366796` | `(780,495)`: Mac `[0,0,0,10]`, Windows `[10,0,0,10]` |
| `case_0029` | `812ff8bec3bac86d1f87804ef3ae52756dfbfd941b61206ff684754eecef56b1` | `23` | `226475` | `(987,496)`: Mac `[7,0,60,64]`, Windows `[7,0,63,67]` |

`case_0015 (1107,315)` is a second live residual control: Mac `[0,0,0,1]`
versus Windows `[0,1,0,1]`. For `case_0001`, the first residual is Mac
`[57,0,0,57]` versus Windows `[56,0,0,56]`; the live `(0,0)` callback can
anchor the row base needed to derive that output address.

The live labels above come from raw CDB records beyond the summarized
`first16`: `case_0015 (780,495)` is callback index `17`, its `(1107,315)`
control is index `20`, and `case_0029 (987,496)` is index `10`.

## Format Drift

The top-level return uses `kind=coordinate_liveness_census_parser_fixture`
instead of the canonical runner success kind `coordinate_liveness_census`.
The material request contract is present and internally consistent, so this
return is accepted with `format_drift=true`. A dedicated fail-closed classifier
must validate this shape before future intake treats it as evidence.

## Next Allowed Action

Run one hash-pinned 8bpc typed-boundary request over the three localized
residuals: derive `case_0001 (17,0)` from live anchor `(0,0)`, and directly
capture census-confirmed `case_0015 (780,495)` and `case_0029 (987,496)`.
Require the truthful PF8 chain `ENTRY_FIELD_ADDR_SNAPSHOT / FIELD_READ_INPUT /
SOURCE_READ / COMPOSE_PRE_U8_SCALE / U8_PRE_STORE / POST_STORE`, with a PF32
zero-count control and retained raw logs. Do not retry `(397,281)` and do not
change production image math from this census alone.
