# OLMColorKey Edge Blur 2.0 — all depths

Status: **pass**

Scope: 4x3 single black key, Edge Blur 2.0, PF8/PF16/PF32 actual full worker through production SmartRender; internal metric/direction planes, exact final alpha, and row padding. No general amount or AE-host claim.

PF8/PF16 independently retain the Blur 1.0 final quantization because native integer metric seeds advance by 255 per pixel; PF32 uses pixel units and exposes the nontrivial distance-1 shell.
