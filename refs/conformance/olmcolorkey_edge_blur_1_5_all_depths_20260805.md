# OLMColorKey Edge Blur 1.5 — all depths

Status: **pass**

Scope: 4x3 single black key, noninteger Edge Blur 1.5, PF8/PF16/PF32 actual full worker through production SmartRender; internal metric/direction planes, exact final alpha, and row padding. No interpolation, general amount, or AE-host claim.

PF8/PF16 use independently observed 255-per-pixel metric seeds. PF32 exposes a negative distance-1 direction shell and final alpha above one; neither value is inferred from Blur 1.0 or 2.0.
