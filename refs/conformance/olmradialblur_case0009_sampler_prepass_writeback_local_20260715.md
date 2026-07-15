# OLMRadialBlur case0009 sampler/prepass/writeback local analysis

- Evidence class: `local_fixture`
- Status: `pass`
- Classification: `local-invariant-proven`

The analyzer checks bilinear weight geometry and the local producer relation `final.rgb = accum.rgb / accum.alpha`, `final.alpha = denom` when defined. For the existing local producer fixture, sampler geometry is intentionally not claimed because it has no output-coordinate rows. It does not make an AE-exact claim.

- `record 0`: `pass`, producer cells checked `1`
- `record 1`: `pass`, producer cells checked `1`
- `record 2`: `pass`, producer cells checked `1`
- `record 3`: `pass`, producer cells checked `1`
