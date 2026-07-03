# OLMRadialBlur Tiny Rotation Anchor Context/Watch Follow-up Contract - 2026-07-02

This follow-up replaces the earlier anchor-pointer retry after that return came
back `failed_partial` with a still narrower retry shape.

Target:

- request id:
  `olmradialblur_tiny_rotation_anchor_context_watch_followup_20260702`
- case:
  `case_0010`
- witness:
  `(1614,6)`
- stable anchor:
  `OLMRadialBlur+0x4eb9/+0x4ec8`

Wanted proof:

1. at the stable anchor, dump `rsi`, `rbp`, `rsp` qword windows plus any
   polar-grid, row-base, and metadata pointers before continuing
2. compute the exact sampled-cell address for source xy
   `[1603.8396,844.3175]`
3. set the narrowest read/write watchpoints on that sampled cell and adjacent
   row cells before final inverse sampling
4. retain the first upstream promotion branch that can still turn the
   near-black anchor into the final white output

Actionable return must include:

- the stable anchor plus the dumped anchor context used to reconstruct the
  sampled-cell address
- concrete sampled-cell address and adjacent-row addresses
- typed values for:
  - substitute/fallback or source-population decision
  - preserved validity at `+0xf252`
  - accumulated RGBA at `+0xf250`
  - normalized final polar RGBA at `+0xe`
- the exact failed address/condition if the watchpoint path still cannot be
  held

Forbidden until this lands:

- broad Rotation PNG tuning
- reopening Zoom denominator tuning from this lane
- retuning writeback from final bytes alone
