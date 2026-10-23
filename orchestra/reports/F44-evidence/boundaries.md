# F44 import boundaries

Facts from the MAIN read-only disassembly/decompilation and current source:

- DirectionalBlur has `cosf(param_5)` / `sinf(param_5)` in both scalar and RGBA rotation helpers (decomp lines 359–360 and 527–528). `core/dblur_rotate.cpp` formerly computed double sin/cos followed by a float cast. Both entry points now call the corresponding UCRT float API in FMA mode.
- ColorKey has `sinf` in the three typed Around callbacks (decomp lines 1529, 1712, 1895). The recovered shared typed path documents `FUN_180005550`. Its FLOAT32 phase and post-sine add/multiply remain unchanged. Direction-2 fallback calls use the same float boundary. Inside/Outside recovered paths explicitly use double phases and double sin, and are unchanged. Other fallback curves and historical constants are unchanged.
- RadialBlur `FUN_180009a10` loads FLOAT32 2^32 from RVA 0x216d4, calls imported log2f through IAT 0x21198, divides FLOAT32 24 (RVA 0x216d0) by that return, takes ceil and clamps the number of MT draws to at least one. The constants are hash-bound in `radial-log2-boundary.json`. Thus log2f(2^32)=32 yields one draw. The Mac equivalent in `core/dblur_noise.h` already implements this fixed MT19937 specialization as one draw and FLOAT32 division by 2^32; there is no host log2f call to replace. No new dynamic computation is introduced into that specialized path.
- RadialBlur double sin/cos, including calls whose results are later converted to float, remain unchanged. DistanceGradation and KiraKira are unchanged.
- The F44 worker patch replaces the three legacy callbacks and adds the three native Win64 callbacks/dispatch names, using the existing safe FFI module and mode selection. The legacy dispatcher recognizes both `api-ms-win-crt-math-l1-1-0.dll` and `ucrtbase.dll`; native dispatch uses export names as in F30.

Inference: differences between unchanged-parent F32 and F44 successful original-AEX output are isolated to this three-function import set. A changed execution status is not automatically attributed to math. Native-carrier numerical execution is separate from the arm64 Unicorn validation.
