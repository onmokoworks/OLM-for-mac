# OLMDistanceGradation PF16 blur/background family

Status: `exact`, bounded actual-AEX helper/callback replay to production.

The fixture is a 17x11 PF16 source with a central 9x7 transparent island,
146-byte input rows, 150-byte output rows, and `0xA5` padding. Parameters fix
Inside/RGB, threshold 4, invert on, Blur Size 2, and downsample 1/2. Eight
cells cross Constant/Linear, Background off/on, and Blur Mode 2/3.

The hash-pinned 2025 AEX executes `FUN_181174760`, legacy `cvSmooth`
`FUN_1812864d0`, PF16 nearest-even staging, and all 187 calls to
`FUN_181170480`. Production matches 1,650/1,650 bytes in every cell, including
padding. The four pre-blur/blur/staged surface hashes and eight final active
hashes are pinned in
`test_olmdistancegradation_classic_pf16_blur_background_family_20260810.py`;
all four blurred surfaces and all eight outputs are pairwise distinct.

The family proves these bounded behaviors:

- Blur Mode 2 selects normalized box blur; Blur Mode 3 selects Gaussian,
  independently of interpolation.
- Both modes convert full-resolution Blur Size using the downsample ratio;
  size 2 at 1/2 gives the actual 3x3 kernel.
- Legacy Gaussian 3x3 uses exact `[1,2,1]/4` coefficients and replicated
  borders.
- PF16 Inside/RGB hidden-color and non-Constant blurred-field channel behavior
  follows the actual typed callback for both Background states.

Excluded: other kernels, anisotropic downsample, other ownership/render modes,
PF8/PF32 extrapolation, PF32 SmartRender, and AE import/export behavior.
