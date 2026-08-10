# OLMDistanceGradation exported upstream owner seam

Status: **PF8_EXPORTED_SMART_OWNER_CONSTANT_4_EXACT_LINEAR_4_RESIDUAL_PF16_PF32_EXCEPTION_BOUNDARY**.

The unchanged Windows AEX now completes exported SmartPreRender/SmartRender for the full PF8 Constant/Linear × Blur 2/3 × Background off/on product. The four Constant 17×11 tight buffers match the production numerical chain byte-for-byte. All four Linear cells complete but retain distinct hashes from the manually assembled fieldgen/blur/compose chain, exposing a real upstream-owner residual rather than an import or suite gap. The six optional OpenCV 4.5.5 parallel backend DLL candidates are absent, return `NULL + ERROR_MOD_NOT_FOUND`, and correctly fall back to the built-in backend.

PF16 and PF32 representative exported Smart runs stop in the actual AEX through `_CxxThrowException` before output. This does not invalidate their separately exact eight-cell numerical evidence: PF16 is covered through the fieldgen/blur/typed-compose chain, and PF32 through classic whole owner `FUN_181172a10`. The actual AEX has no PF32 SmartRender branch. No external PE was loaded and no native AE execution is claimed.
