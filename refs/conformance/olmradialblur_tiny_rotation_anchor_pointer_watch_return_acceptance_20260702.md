# OLMRadialBlur Tiny Rotation Anchor Pointer/Watch Return Acceptance - 2026-07-02

Judge `olmradialblur_tiny_rotation_anchor_pointer_watch_followup_20260702`
like this.

`answered`

- the return keeps the stable inverse-sampler anchor
- and it exposes enough dumped pointer/watchpoint context to reconstruct the
  sampled-cell address and isolate the first upstream promotion branch for
  `case_0010 (1614,6)`
- with typed values for the branch path (`+0xf252`, `+0xf250`, `+0xe`, or an
  equivalent substitute/source-population branch)

`failed_partial`

- the return preserves the anchor and some pointer reconstruction facts
- but it still does not isolate the first upstream branch/value that promotes
  the witness from near-black to white

`trace-too-sparse` / `not isolated`

- only the same near-black inverse-sampler sample
- only the final white byte
- no concrete sampled-cell address or neighboring-row addresses
- no exact failed address/watchpoint condition

Do not treat repeated anchor-only confirmation as answered.
