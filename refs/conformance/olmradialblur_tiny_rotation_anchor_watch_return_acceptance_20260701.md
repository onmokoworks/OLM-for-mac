# OLMRadialBlur Tiny Rotation Anchor Watch Return Acceptance - 2026-07-01

Judge `olmradialblur_tiny_rotation_anchor_watch_followup_20260701`
like this.

`answered`

- the return starts from the known inverse-sampler witness chain
- and it preserves enough stack/pointer/watchpoint context to isolate the first
  upstream promotion branch for `case_0010 (1614,6)`
- with typed values for the branch path (`+0xf252`, `+0xf250`, `+0xe`, or an
  equivalent substitute/source-population branch)

`failed_partial`

- the return preserves the anchor and some surrounding pointer context
- but it still does not isolate the first upstream branch/value that promotes
  the witness from near-black to white

`trace-too-sparse` / `not isolated`

- only the same near-black inverse-sampler sample
- only the final white byte
- no concrete stack/pointer/watchpoint facts
- no exact failed watchpoint condition

Do not treat a repeated anchor-only confirmation as answered.
