# OLMRadialBlur Type3 all-depth bounded public closure

Status: `pass`

Exact 9x7 Zoom Type3/NV25 source+Layer pairs are raw exact: PF8 15, PF16 15 and PF32 15.
The Windows side is a pinned AEX typed direct owner under repository AexLoader/Unicorn; no native AE or installed-runtime claim is made.
Classic EffectMain and SmartPreRender-to-SmartRender both reproduce the same padded typed output at all three depths.
Every depth is exact source+Layer-pair bounded. Other Type3 states remain fail-closed.

Production source: `b74b3d2c7ea6724593b28f82d36615e071e18d813e5b99cc948e26a447fdb0d1`
Rows: `ac9651a8b544224bb619f4740cebb3cc4a06eedb4d11bba1bce83279174f94cf`
