# OLMDistanceGradation public Smart owner contract

Status: **PASS_ACTUAL_PUBLIC_PF32_SMART_OWNER_BOUNDED_56_RAW_EXACT_8_POWER_FAIL_CLOSED**.

The corrected actual-AEX public chain is command 0x18 → `FUN_181173d20` → PF32 `FUN_181172a10` → iterateFloat/`FUN_181170c90`. Production admits 56 fixed 17×11 cells: PF16 32 and non-Power PF32 24. The eight PF32 Power cells fail closed on both architectures because the AEX imports Windows UCRT `powf` while AEXCompat substitutes host `f32::powf`; no native Windows UCRT result is retained. Public EffectMain tests cover six admitted PF32 Mode 5 positives, eight Power rejects with input/output/padding unchanged, balanced world/parameter lifecycle including exception cleanup, suite-error propagation, format and layout guards, twenty-one other negative cases, and four classic guards. Unlisted tuples, partial worlds, native AE pixels, and the CLI Mode 4/5 path remain unpromoted.
