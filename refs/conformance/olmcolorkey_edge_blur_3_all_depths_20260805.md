# OLMColorKey Edge Blur 3.0 — all depths

Status: **pass**

Scope: 4x3 single black key, Edge Blur 3.0, PF8/PF16/PF32 actual full worker through production SmartRender; exact internal distance/direction planes, final alpha, padding, and AEX hash. No interpolation, general amount, or AE-host claim.

PF32 has independently observed distance-1 and distance-2 shells; distance 3 is cut off at amount 3.0. Integer depths retain 255-per-pixel metric seeds.
