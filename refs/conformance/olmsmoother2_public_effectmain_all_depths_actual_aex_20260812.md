# OLMSmoother2 public EffectMain all-depth covering

Verdict: `PASS_6_PUBLIC_EFFECTMAIN_SMARTPRE_SMARTRENDER_ALL_DEPTHS_ACTUAL_AEX_CORE_EXACT`

Six padded 17x11 semi-transparent cases (two per depth) cross Version 1/2, Gamma None/All/Colors, key off/non-invert/invert, palette count 1/5 with reorder/duplicate, default/mixed smoothing, and straight/native-premultiplied inputs. Production `EffectMain(SmartPreRender -> SmartRender)` matches the actual-AEX core raw bytes or PF32 float words in all cases. Input bytes and row padding remain unchanged/preserved; callback counts and result/max-result rectangles are exact.

The same PF8/PF16/PF32 parameters are rejected through classic Render and leave output untouched, matching the exported entry ownership boundary. SmartPreRender owns no pre-render allocation, so no free callback applies. AE-host execution and unlisted combinations are not generalized.
