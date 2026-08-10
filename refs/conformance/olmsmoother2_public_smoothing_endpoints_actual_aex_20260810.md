# OLMSmoother2 public smoothing endpoints

Verdict: `PASS_PUBLIC_RANGE100_AND_EXTRA0_100_INDEPENDENT_EFFECT_ALL_DEPTHS_EXACT`

On one fixed padded 5x5 fixture, PF8/PF16/PF32 each produce three distinct raw outputs for baseline `Range=2, Extra=0`, public `Range=100, Extra=0`, and public `Range=2, Extra=100`. Range 100 changes the naturally generated class plane. Extra Smooth 100 preserves that plane but independently changes the worker output. Every variant is byte-exact between the checked-in AEX natural path and production.

The evidence is limited to this fixture and does not claim other parameter interactions or AE-host execution.
