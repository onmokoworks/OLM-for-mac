# OLMDistanceGradation exported typed owner matrix

Status: **PASS_PF16_PF32_EXPORTED_SMART_OWNER_16_CELL_EXACT**.

The unchanged Windows AEX completed exported SmartPreRender/SmartRender for PF16 and PF32 across Constant/Linear × Blur 2/3 × Background off/on. All sixteen tight 17×11 buffers match production `RenderBits` byte-for-byte. PF16 acquires `PF iterate16 Suite` v1 and PF32 acquires `PF iterateFloat Suite` v1; no `_CxxThrowException` continuation or exception swallowing is used. This proves the bounded production RenderBits tuples only; Mac PF32 Smart admission and field staging remain a separate evidence boundary.
