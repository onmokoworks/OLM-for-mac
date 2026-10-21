# OLMKiraKira PF8 source-decode closure（2026-08-12）

Status: **raw exact**

5×3 `alpha_i_over_17` と既存半透明fixtureに限定し、PF8 byte laneを`f32(byte * f32(1/255))`で読むWindows規則を自然AEX source planeで固定した。alpha fixtureはdivision counterfactualより7 wordsが各1 ULP高い。修正後はseed→Mode 1 Highlight ray→fd90 glow→compose/writer→public PF8がraw exactで、同じpublic tupleのPF16/PF32もexact。既存半透明3-depth hashも不変。
