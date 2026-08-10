# OLMSmoother v1 multivalue ramp boundary

Verdict: `PASS_PF8_PF16_MULTIVALUE_RAMP_ALL_20_CELLS_EXACT`

PF8 and PF16 are byte-exact in all twenty key/tolerance cells. PF16 retains the Windows scalar-SSE rounding points in `AlphaBlend16`. PF8 now follows the AEX scalar-SSE operation boundaries and its signed-luma truncation-toward-zero imports in `ColorCompare8`; this restores the missing caller executor callbacks without pixel-specific handling.
