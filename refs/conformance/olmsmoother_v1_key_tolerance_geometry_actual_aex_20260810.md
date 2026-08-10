# OLMSmoother v1 Color Key × smoothing × geometry boundary

Verdict: `PASS_V1_EFFECTIVE_COLOR_KEY_TOLERANCE_GEOMETRY_PF8_PF16_EXPORTED_EFFECTMAIN_EXACT`

A padded nonuniform 7×5 fixture crosses effective Color Key off/on and Do Smooth Range 0/1/6/127/255 at PF8 and PF16 through the actual exported Windows AEX `PF_Cmd_RENDER` and production `EffectMain`. Active pixels and row padding are byte-exact in all 20 cells. Key, tolerance and main-kernel effects are independently non-vacuous.

PF32, other key colors/geometries and AE host/export color management remain unclaimed.
