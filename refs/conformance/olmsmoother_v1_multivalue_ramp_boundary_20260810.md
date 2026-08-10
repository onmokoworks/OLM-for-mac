# OLMSmoother v1 multivalue ramp boundary

Verdict: `PASS_PF16_MULTIVALUE_RAMP_FMA_EXACT_PF8_RESIDUAL_RECORDED`

PF16 is byte-exact in all ten key/tolerance cells after retaining the Windows scalar-SSE rounding points in `AlphaBlend16`. PF8 remains explicitly open at tolerance 6: both key states differ by nine RGB bytes; the other eight PF8 cells are exact. No PF8 workaround is admitted.
