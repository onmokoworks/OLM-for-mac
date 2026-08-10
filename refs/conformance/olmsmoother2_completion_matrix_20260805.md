# OLMSmoother2 completion matrix

| Area | Proven | Remaining boundary |
|---|---|---|
| Commands | Dynamic production EffectMain PF16 classic chain and PF32 SmartRender callback/parameter chain, both joined to actual AEX core and installed identity | Actual-AEX exported entry and AE-host execution are not claimed |
| Versions | v1 and v2 actual classifier/worker → production for PF16/PF32 | No new host claim |
| Depths | PF8 v1/v2 natural classifier → c280 → typed worker → production on padded 3x2 fixtures; PF16 and PF32 current emulation fixtures | Other PF8 geometry and parameter interactions |
| Key | non-invert/invert thresholds, non-invert and invert white endpoints, both Gamma Colors interactions including invert-white; PF8 non-invert/invert key + Gamma Colors 3x2 fixtures | Other color endpoints and larger interaction cross-products |
| Gamma | None, All Colors, Gamma Colors, values 1.0, retained case-09 intermediate 1.9328, and 2.4; PF8 Gamma All and Gamma Colors with both key polarities | Other intermediate values and PF8 cross-parameter combinations |
| Smoothing | Smoothness 0/100, Range 0/1/255, Extra Smooth 0/100 | Other cross-parameter combinations |
| Palette | natural counts 1..5, reorder, duplicate, tolerance | Count 6 is direct-owner-only and forbidden publicly |

The largest gap closed in this round is the public `Extra Smooth=100` upper endpoint. It is actual-AEX → production exact for PF16/PF32 with LUTs and padding fixed. The fixture does not claim that Extra Smooth independently changes these particular output bytes.

The subsequent `Smooth Range=255` upper endpoint is also exact and does show an independent effect: its class plane becomes all zero and its PF16/PF32 raw outputs differ from both Range 0 and Range 1 fixtures.

The 2026-08-10 focused PF8 fixture closes the previously listed consolidated-depth gap for both v1 and v2. It uses naturally generated nonzero class planes, the checked-in AEX PF8 worker, production `RenderBits<PF_Pixel8>`, non-tight rowbytes, and (for v2) the captured LUT pair. This does not generalize to other PF8 geometry or parameter interactions.

A second 2026-08-10 fixture connects PF8 v2 non-invert and invert key ownership to Gamma Colors, natural classifier/c280, LUT-backed typed output, and production. It also fixes the observed PF8 boundary that code 0 versus key code 1 is outside the strict key-match threshold. Other key colors, palettes, geometry, and key plus Gamma All interactions remain unclaimed.

The PF8 Gamma All fixture closes that remaining primary gamma-mode depth gap for key-off, gamma 2.4, Smoothness 100, Range 1, Extra Smooth 0 on a padded 3x2 input. Other PF8 gamma values, geometry, smoothing combinations, and key interactions remain unclaimed.
