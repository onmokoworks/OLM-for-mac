# OLMColorKey Edge Blur 2.5 — all depths

Status: **pass**

Scope: 4x3 single black key, Edge Blur 2.5, PF8/PF16/PF32 actual full worker through production SmartRender; exact internal distance/direction planes, final alpha, padding, and AEX hash. No interpolation, general amount, or AE-host claim.

PF32 independently exposes positive distance-1 and negative distance-2 direction shells, yielding both sub-one and above-one final alpha. Integer depths retain 255-per-pixel metric seeds and no nonzero neighbor shell.
