# OLMRadialBlur tiny Rotation Backstep Return Acceptance - 2026-07-01

Judge `olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701`
like this.

`answered`

- the return starts from the known inverse-sampler witness chain and then
  isolates a typed upstream branch/value that can still explain the final white
  pixel at `case_0010 (1614,6)`
- this may be substitute/fallback, neighboring-row ownership, or another
  pre-inverse-sample source-population decision

`failed_partial`

- the return reconfirms the anchored inverse-sampler hit and/or final white byte
- but it still does not isolate the first upstream branch/value that changes the
  witness from near-black to white

`trace-too-sparse` / `not isolated`

- only final bytes
- only the same inverse-sampler sample
- no retained upstream branch/value
- no exact failed hook reason

Do not treat repeated confirmation of the same near-black inverse-sampler value
as an answered state by itself.
