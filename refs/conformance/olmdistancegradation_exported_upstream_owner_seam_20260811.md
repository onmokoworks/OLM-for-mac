# OLMDistanceGradation exported upstream owner seam

Status: **PASS_PF8_EXPORTED_SMART_OWNER_8_CELL_EXACT_PF16_PF32_EXCEPTION_BOUNDARY**.

The unchanged Windows AEX now completes exported SmartPreRender/SmartRender for the full PF8 Constant/Linear × Blur 2/3 × Background off/on product. All eight 17×11 tight buffers match the production whole chain byte-for-byte. The six optional OpenCV 4.5.5 parallel backend DLL candidates are absent, return `NULL + ERROR_MOD_NOT_FOUND`, and correctly fall back to the built-in backend.

The former Linear-only residual was localized after field generation and blur: the green lane and output alpha already matched, while production/manual staging left the compose auxiliary red lane at zero. The actual owner stages blurred `X` into that lane too. Production now passes blurred `X` as PF8 Linear+blur `field_aux` and preserves it in the zero-ownership RGB branches, closing all four complete buffers.

PF16 and PF32 representative exported Smart runs stop in the actual AEX through `_CxxThrowException` before output. This does not invalidate their separately exact eight-cell numerical evidence: PF16 is covered through the fieldgen/blur/typed-compose chain, and PF32 through classic whole owner `FUN_181172a10`. The actual AEX has no PF32 SmartRender branch. No external PE was loaded and no native AE execution is claimed.
