# OLMSmoother2 actual exported owner seam

Verdict: `PASS_ACTUAL_EXPORTED_SMART_OWNER_VERSION_KEY_GAMMA_SMOOTHING_ALL_DEPTHS_EXACT`

The unchanged Windows AEX exported `SmartPreRender`/`SmartRender` owner materializes the compound parameters and produces complete tight PF8, PF16, and PF32 buffers. Version 1 + non-invert key and Version 2 + invert key representatives match production `RenderBits` byte-for-byte (float-bit-for-float-bit for PF32). All six runs complete with no unsupported suite calls.

The legacy `PF_Cmd_RENDER` dispatch target is a literal success no-op; the numerical public owner is Smart Render. Required callbacks exercised here are the global PF Handle owner, parameter checkout/checkin, Smart checkout callbacks, PF World Suite typed primary worlds, ColorParamSuite, and VCOMP scheduling. AEXCompat was used read-only and was not modified.

This focused 5x5 owner fixture does not supersede the July `legacy_case_0012` Mac-AE host residual.
