# OLMSmoother2 v2 Gamma Colors duplicate palette

Verdict: `PASS_V2_GAMMA_COLORS_DUPLICATE_ORDER_FIRST_MATCH_TO_PRODUCTION_EXACT`

The independent ordered palette `[white, red, white]` proves first-match semantics: actual-AEX white-match instruction count equals a single-white control, despite the duplicate last entry. PF16/PF32 natural frame paths, LUTs, padding, and production bytes are exact.

Tolerance ties, other duplicate layouts, key interaction, and AE host are unclaimed.
