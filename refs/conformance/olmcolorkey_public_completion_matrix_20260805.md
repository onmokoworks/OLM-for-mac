# OLMColorKey public completion matrix

Current bounded evidence covers Smart PreRender/SmartRender and all public Edge Blur directions 0–4 at amount 2.0 for a 4×3 single-black-key fixture in PF8, PF16, and PF32. Direction 2 additionally has all-depth captures for amounts 0.5 through 4.0 in 0.5 increments.
Direction 1 additionally has an independent all-depth exact capture at amount 1.0.
Direction 2 amount 2.0 also has an independent center-key `(1,1)` geometry capture; it does not widen the corner-key gate to arbitrary positions or dimensions.

| Direction | Amount 2 PF8 | PF16 | PF32 |
|---|---:|---:|---:|
| 0 | exact | exact | exact |
| 1 | exact | exact | exact |
| 2 | exact | exact | exact |
| 3 | exact | exact | exact |
| 4 | exact | exact | exact |

The largest remaining class is non-direction-2 amounts and shapes beyond the captured amount-2 single-key boundary, followed by general geometry and AE-host execution. For the independent center-key all-depth fixture, public `PF_Cmd_RENDER` now produces a full-buffer byte-exact result to the proven SmartRender path and therefore reaches the same typed `RenderWorld` writer.

This matrix inventories bounded evidence only; it does not generalize equality between directions or claim every parameter combination.

The current source rebuild and installed Universal bundle have byte-identical `__text` and `__const` sections for both x86_64 and arm64. This connects the actual entry/worker/writer evidence and production EffectMain adapter to the installed executable. After Effects was absent, so loaded-module and current AE-render identity remain explicitly unclaimed.

The Mac host runner, pinned to installed SHA `34fd47cd…`, completed After Effects `26.3.0.87` Software/16bpc case0001. Fresh output SHA `d650ed20…` was exact, with PID `60573`, sole exact loaded-module mapping, and unchanged installed hash verified before and after rendering. This promotes only that case to a current-binary Mac AE exact result.
