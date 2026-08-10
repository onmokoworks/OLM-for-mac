# OLMSmoother2 Version × key × Gamma Colors × smoothing boundary

Verdict: `PASS_VERSION1_2_KEY_POLARITY_GAMMA_COLORS_SMOOTHING_ALL_DEPTHS_EXACT`

A padded 5x5 fixture crosses Version 1/2, non-invert/invert Color Key, Gamma Colors `[red,key]` at 2.4, and public Smoothness/Range/Extra Smooth upper endpoints. PF8/PF16/PF32 actual AEX key owner, natural classifier, and typed worker match production byte-for-byte. Non-invert Version 1/2 and both key polarities are distinct at every depth. The one-retained-pixel invert fixture is version-equivalent at PF8/PF16 but version-distinct at PF32; this equivalence is recorded rather than generalized.

This synthetic core fixture does **not** supersede the July `legacy_case_0012` Mac-AE residual. That record uses different practical geometry/descriptor and includes the AE host boundary, which remain independently scoped.
