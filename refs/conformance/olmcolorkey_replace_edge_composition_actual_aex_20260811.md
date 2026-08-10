# OLMColorKey Replace × Edge composition

Status: **exact**

Replace changes RGB while preserving the Edge-derived alpha topology in every depth/mode pair. Each nonzero Edge mode independently differs from no Edge. Thin ±4 saturates this compact fixture to a uniform matte, so each simultaneous output equals Thin-only; nevertheless every actual-AEX depth executes the Blur handle lifecycle after Thin, PF16 executes all 143 captured Blur apply callbacks, and the intermediate temporary-world hashes are retained per case. This proves the composed stage is executed rather than skipped. The actual Windows AEX full worker and production `RenderWorld` are raw-exact in all 36 cells.

Boundary: Exact for the declared 13x11 two-key fixture, Replace off/on, Edge none/Thin -4/Thin +4/Blur Direction 2 Amount 4, the two Thin+Blur combinations, and PF8/PF16/PF32. Other directions, amounts, geometry, and AE-host execution are not claimed.
