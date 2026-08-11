# OLMDistanceGradation exported typed owner matrix

Status: **PASS_56_CELL_EXACT_8_PF32_MODE5_FAIL_CLOSED**.

The unchanged Windows AEX completed exported SmartPreRender/SmartRender for PF16 and PF32 across Constant/Linear/Sphere/Power × Blur 2/3/4/5 × Background off/on. All 32 PF16 buffers and the 24 PF32 Blur 2/3/4 buffers match production `RenderBits` byte-for-byte. The eight PF32 Blur Mode 5 cells execute in the actual AEX but production rejects them with `PF_Err_BAD_CALLBACK_PARAM`: the OpenCV 4.5.5 SIMD bilateral plane remains one-ULP different on part of this fixture and is not admitted as exact. PF16 acquires `PF iterate16 Suite` v1 and PF32 acquires `PF iterateFloat Suite` v1; no `_CxxThrowException` continuation or exception swallowing is used. This proves the bounded production RenderBits tuples only; native Mac AE PF32 SmartRender host execution and field staging remain a separate evidence boundary.
