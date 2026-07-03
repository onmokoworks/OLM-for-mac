# OLMRadialBlur Tiny Rotation Anchor Watch Follow-up Contract - 2026-07-01

This follow-up starts from the already stable inverse-sampler anchor and asks
for the next thing the previous return could not hold: the concrete pointer /
watchpoint context that exposes the first upstream promotion branch.

Target:

- request id:
  `olmradialblur_tiny_rotation_anchor_watch_followup_20260701`
- case:
  `case_0010`
- witness:
  `(1614,6)`
- stable anchor:
  `OLMRadialBlur+0x4eb9/+0x4ec8`

Wanted proof:

1. retain stack/pointer context for the sampled polar cell and neighboring rows
2. attach the first upstream branch that can still turn the witness from
   near-black to white
3. record typed values for:
   - substitute/fallback or source-population decision
   - preserved validity at `+0xf252`
   - accumulated RGBA at `+0xf250`
   - normalized final polar RGBA at `+0xe`
   - concrete row/angle/cell addresses feeding the branch

Actionable return must include:

- the stable anchor plus concrete stack/pointer facts
- typed upstream branch values, not just the repeated near-black sample
- the exact failed pointer/watchpoint condition if the branch still cannot be held

Forbidden until this lands:

- broad Rotation PNG tuning
- reopening Zoom denominator tuning from this lane
- retuning writeback from final bytes alone
