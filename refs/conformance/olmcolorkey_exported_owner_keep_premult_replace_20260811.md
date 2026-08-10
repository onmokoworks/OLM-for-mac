# OLMColorKey actual exported owner seam

Verdict: `EXACT_EXPORTED_OWNER_ALL_DECLARED_TOGGLE_DEPTH_CELLS`

All 24 Color Keep × Premultiplied × Replace × PF8/PF16/PF32 cells pass through exported SmartPreRender and SmartRender and produce complete buffers exactly equal to production `RenderWorld`. The 11x7 fixture includes fractional and low alpha, alpha-zero hidden RGB, rejected near-key color, and asymmetric background. PF16 and PF32 exercise `PF iterate16 Suite` v1 and `PF iterateFloat Suite` v1 through AEXCompat commit `0ee27894`.

The paired declared-record full-worker matrix separately proves eight-byte row-padding preservation; exported `render-png` worlds are tightly packed. This does not claim arbitrary parameter products, native Windows execution, or After Effects host execution.
