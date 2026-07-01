# OLMRadialBlur tiny Rotation Bright-Lobe Search

Date: 2026-06-30

Goal:

- Decide whether the tiny Rotation high-max witness could still be explained by
  a small local output shift, or whether the bright contribution is absent
  altogether in the current candidate.

Search region:

- center: witness `(1614,6)`
- local lobe listing: around `(1614,6)` in a small patch
- wider candidate search: `25x25` region centered on the witness

## Reference bright lobe

Reference pixels with `R >= 240` in the local witness area:

- `(1610,2)=247`
- `(1611,3)=247`
- `(1613,3)=245`
- `(1612,4)=251`
- `(1613,4)=247`
- `(1614,4)=253`
- `(1613,5)=253`
- `(1614,5)=251`
- `(1614,6)=255`

Wider `25x25` reference search:

- bright count (`R >= 200`): `17`
- center of mass: `(1611.7433, 2.7515)`

## Candidate search

Wider `25x25` candidate search around the same witness:

- bright count (`R >= 200`): `0`

## Interpretation

- The current candidate does not contain a displaced bright lobe near the
  witness. There is nothing nearby to re-attribute as a simple output shift.
- This strengthens the current local diagnosis:
  - tiny Rotation is not primarily a one-pixel or small-neighborhood placement
    error
  - the relevant bright contribution family is absent or numerically suppressed
    upstream of final inverse sampling
