# OLMColorKey Replace × Edge composition

Status: **exact**

Replace changes RGB while preserving the Edge-derived alpha topology in every depth/mode pair. Each nonzero Edge mode independently differs from the no-Edge topology. The actual Windows AEX full worker and production `RenderWorld` are raw-exact in all 24 cells.

Boundary: Exact for the declared 13x11 two-key fixture, Replace off/on, Edge none/Thin -4/Thin +4/Blur Direction 2 Amount 4, and PF8/PF16/PF32. Other simultaneous Thin+Blur settings, directions, amounts, geometry, and AE-host execution are not claimed.
