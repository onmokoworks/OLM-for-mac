# OLMDistanceGradation PF32 Power native-UCRT public closure

Status: **PASS_NATIVE_UCRT_ACTUAL_XMM_EXPORTED_AEX_MAC_PUBLIC_RAW_EXACT_8_OF_8**.

The validated 64-bit Windows UCRT return differs from macOS/libSystem at one of 63 exact `powf` pairs. All 992 actual-AEX XMM calls map to that native table. Replaying the same table through the exported Windows AEX and current Mac body, then through the public SmartRender contract, closes all eight fixed 17x11 PF32 Power cells at full 2,992-byte RAW identity. Input immutability, row padding and callback cleanup remain closed. Admission is limited to the named tuple/source mask; no install or After Effects launch occurred.
