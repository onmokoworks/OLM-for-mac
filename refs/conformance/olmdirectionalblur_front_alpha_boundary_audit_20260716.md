# OLMDirectionalBlur Front Alpha Fade boundary audit

## Verdict

- Selected lane: `Front Alpha Fade`
- Status: `pass`

## Commands

`python3 tools/emulation/test_dblur_front_alpha_boundary_audit_20260716.py`

## FACT

- The same-run Windows host-boundary proof for db_angle0_alpha_fade_hard_edges loaded the pinned 2025 AEX and both host formulas are exact (max_diff=0 in and out).
- The bounded actual-AEX Front Alpha Fade witness rerun is byte-exact for rowdriver destination, denominator, alpha, and normalization against the portable harness.
- The decomp rowdriver calls FUN_180001000 with +0x3ed8/+0x4c and +0x7ee8/+0x54, while the scatter taper path uses +0x40 before FUN_1800013e0.
- The current software 24fps reference case keeps front Sharp Tail, all Back controls, and Noise Variation at zero while Front Alpha Fade is 96.
- The imported 32bpc Windows family remains fully mixed across variation/fade/tail/back/noise (10/10 for each family), so those broader lanes are not isolated by the current float return set.

## INFERENCE

- Front Alpha Fade is the smallest remaining DirectionalBlur lane that can be closed today with existing AEX, decomp, and harness evidence because it already has an exact bounded AEX replay and a pinned same-run host boundary.
- Size Variation, Sharp Tail, Back, and Noise still require either a narrower typed witness or a less entangled return set before the same style of closure is justified.
- The remaining Front Alpha Fade gap is downstream of the bounded rowdriver/normalization witness; this audit does not convert that lane into an AE-exact claim.

## Witness replay

- Rowdriver status: `pass`
- Rowdriver exact: `True`
- Normalization exact: `True`
- PF writer vs Windows exact: `False`
- PF writer differing values: `226`

This audit is bounded evidence only. It does not change production source or
promote an AE-exact claim for Front Alpha Fade.
