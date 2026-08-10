# OLMDistanceGradation exported typed owner matrix

Status: **PASS_PF16_PF32_EXPORTED_SMART_OWNER_16_CELL_COMPLETE_4_EXACT_12_RESIDUAL**.

The unchanged Windows AEX completed exported SmartPreRender/SmartRender for PF16 and PF32 across Constant/Linear × Blur 2/3 × Background off/on. PF16 Constant is byte-exact in all four cells. PF16 Linear has four complete-buffer residuals, and PF32 has eight; these are now render-path differences rather than host ABI failures. PF16 acquires `PF iterate16 Suite` v1 and PF32 acquires `PF iterateFloat Suite` v1; no `_CxxThrowException` continuation or exception swallowing is used.
