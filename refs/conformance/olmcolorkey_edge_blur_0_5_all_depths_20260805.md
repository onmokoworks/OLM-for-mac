# OLMColorKey Edge Blur 0.5 — all depths

Status: **pass**

Scope: 4x3 single black key, Edge Blur 0.5, PF8/PF16/PF32 actual full worker through production SmartRender; exact internal distance/direction planes, final alpha, padding, and AEX hash. No interpolation, general amount, or AE-host claim.

All depths independently stop before the distance-1 pixel at amount 0.5. Integer seeds remain 255-per-pixel while PF32 seeds remain pixel-unit distances.
