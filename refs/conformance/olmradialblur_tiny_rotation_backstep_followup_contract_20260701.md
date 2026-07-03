# OLMRadialBlur tiny Rotation Backstep Follow-up Contract - 2026-07-01

This follow-up replaces the broader tiny-only substitute-path ask with one
operational change: start from the already reliable inverse-sampler witness hit
for `case_0010 (1614,6)` and step backward into the first upstream branch that
can still promote the final pixel from near-black to white.

Target:

- request id:
  `olmradialblur_tiny_rotation_inverse_sampler_backstep_followup_20260701`
- case / XY:
  `case_0010 (1614,6)`

Wanted proof:

1. confirm the same anchored inverse-sampler/source-polar hit that already
   yields the near-black sampled RGBA and the final white Windows byte
2. step backward or earlier from that anchor until one of these becomes typed:
   - substitute/fallback promotion
   - neighboring-row source ownership
   - source-population selection before final inverse sampling
3. retain the caller-side chain if visible:
   - `+0xf252`
   - `+0xf250`
   - `+0xe`

Actionable return must include:

- exact case and XY
- exact failed or successful hook point relative to the anchored inverse-sampler hit
- typed values, not only screenshots or final bytes
- one concrete upstream branch/value that is still capable of changing the
  witness from black to white

Forbidden until this lands:

- final-byte tuning
- validity-alpha policy changes
- broad row-coupling promotion
- global outer-lane retuning
