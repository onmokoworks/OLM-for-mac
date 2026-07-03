# OLMDistanceGradation case_0023 Threshold Follow-up Contract - 2026-07-01

This contract narrows the next Windows runtime-trace ask after the current
edge-family-centric `case_0023` package.

## Target lane

- effect: `OLMDistanceGradation`
- case: `olmdistancegradation_extended__case_0023`
- mode:
  - `Interpolation=Constant`
  - `In/Out=Both`
  - `Outside Threshold=0`
- target residual family:
  threshold-side triplet near `(414..416,393)`

## Why this is now the live follow-up

The current shared package is still strongest on the edge family:

- `(1698..1700,7)`
- `inside=1.0 / outside=0.0`

That is useful, but the active lane is no longer just "top-edge boundary".

The narrower remaining ambiguity is the threshold-family triplet:

- `(414,393)` with `raw_inside=35.0142822`
- `(415,393)` with `raw_inside=36.0138855`
- `(416,393)` with `raw_inside=37.0135117`

The local Mac field already flips `field_x` exactly across that transition.
What is still missing is the Windows typed helper-staging / ownership reading
for the same crossing.

## Exact proof boundary

Return typed values that explain the threshold-family ownership rule, not just
the final red/blue endpoint bytes.

At minimum, isolate:

- helper-stage field value before compose
- raw inside and outside distance values at the triplet
- exact threshold/equality/plateau ownership decision
- whether the Constant-only binary fork sees the pixel before or after that
  ownership decision
- field value actually consumed by the compose callback
- compose output RGBA before word store
- final stored RGBA16

## Witness set

- `(414,393)` below-threshold side
- `(415,393)` first above-threshold side
- `(416,393)` further-inside plateau side

If possible, also include one immediate vertical or horizontal contrast point
only if it helps anchor the same threshold crossing. Do not spend the round on
the already well-described top-edge family.

## Not enough

These are explicitly non-actionable for this follow-up:

- final endpoint bytes only
- another copy of the edge-family `(1699,7)` story only
- broad case PNG rerenders without typed staging values
- generic "Constant branch taken" without the decisive threshold-side values

## Mac-side implementation boundary

Do not reopen:

- broad Constant helper rewrites
- global equality tweaks
- final compose/writeback tuning

from this follow-up alone.

The next acceptable code move should be justified by the threshold-family
staging/ownership witness above.
