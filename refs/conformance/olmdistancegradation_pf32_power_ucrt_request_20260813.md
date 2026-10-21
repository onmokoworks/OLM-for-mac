# OLMDistanceGradation PF32 Power UCRT boundary

Status: **PASS_ACTUAL_XMM_BOUND_NATIVE_UCRT_REQUEST_READY_POWER_REMAINS_FAIL_CLOSED**.

The live production body issued 1,496 `powf` calls across the eight fixed 17x11 PF32 Power cells; these reduce to 63 exact float32 input pairs with exponent bits `0x40100000`. Using the pinned AEXCompat host `f32::powf` substitution, all eight production outputs match the exported Smart AEX buffers byte-for-byte. That relation is diagnostic, not a Windows UCRT oracle.

The packaged Windows request evaluates those 63 pairs with native `System32\ucrtbase.dll!powf` and records exact return bits plus DLL identity without launching AE. Actual-AEX pre-call XMM inputs are now bound for all 992 real calls; the seven production-only pairs are output-irrelevant. PF32 Power remains fail-closed until the native result is returned and all eight native-derived public outputs are raw-exact.
