# OLMDistanceGradation PF32 Mode 5 Universal codegen

Status: **PASS_UNIVERSAL_MODE5_CODEGEN_6_EXACT_2_POWER_FAIL_CLOSED**. Both Universal slices retain direct expf, three noncontracting helper calls and zero fused operations for the IPP field; each executes six admitted non-Power Mode 5 cells raw-exact. All eight PF32 Power cells (Blur 2–5 × background off/on) fail closed with output untouched because native Windows UCRT powf evidence is absent. No whole-matrix claim is made.
