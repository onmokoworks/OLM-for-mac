# OLMRadialBlur tiny Rotation Follow-up Contract - 2026-07-01

This contract narrows the next Windows runtime-trace ask after the shared
`olmradialblur_caller_collapse_followup_20260701` return.

That return already made one important split safe:

- Zoom `case_0009` is no longer the best active Windows ask.
- tiny Rotation `case_0010` is still unresolved and still needs upstream proof.

## Target witness

- effect: `OLMRadialBlur`
- path: tiny Rotation
- case: `case_0010`
- witness pixel: `(1614,6)`
- current Mac candidate: `[0,0,0,255]`
- Windows Software reference: `[255,255,255,255]`

## What the previous return already proved

- exact final Windows byte at the witness is white
- closest traced inverse-sampler return is near-black with alpha `1.0`
- this is not explained by a simple final byte conversion rule
- this is not a pure validity-alpha collapse

Do not spend the next Windows round rediscovering only those same facts.

## Exact proof boundary for the next Windows ask

Return an actionable typed chain for the branch that produces the missing
bright lobe before final inverse sampling.

At minimum, isolate one of these two acceptable paths:

1. source-population path:
   - exact polar/source coordinates used for the witness neighborhood
   - which nearby row/cell/neighbor contributions should populate the bright
     lobe
   - whether a border, wrap, substitute, or fallback branch changes that
     source population
   - typed RGB/A values before and after that branch

2. substitute/fallback path:
   - exact branch decision that replaces the near-black inverse-sampler return
   - typed substitute RGB/A or promoted bright value
   - preserved validity at `+0xf252`
   - accumulated `+0xf250` RGBA if present
   - normalized final polar `+0xe` RGBA
   - pre-writeback RGBA float
   - final stored RGBA8

## Strongly preferred concrete fields

- `case_id=case_0010`
- `x=1614 y=6`
- inverse-sampler input XY
- source-polar XY or cell indices for the four contributing cells
- validity/border decision
- fallback/substitute-path fact if taken
- typed RGBA for:
  - source/polar value
  - preserved validity `+0xf252`
  - accumulated `+0xf250`
  - normalized final polar `+0xe`
  - pre-writeback
  - final stored byte

## Not enough

These are explicitly non-actionable for this follow-up:

- final white byte only
- another copy of the same near-black inverse-sampler return only
- "suspected substitute path" without the actual typed branch/value
- neighborhood screenshots or PNGs without the requested typed witness chain

## Mac-side implementation boundary

Do not change:

- final byte conversion
- global validity-alpha policy
- global angular/radial offset

from this lane alone.

The next acceptable Mac-side change should stay inside upstream Rotation
source-population / neighbor-ownership / substitute-path logic and should be
justified by the typed Windows witness above.
