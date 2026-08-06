# OLMSmoother2 Gamma Colors count6 contract cap

Verdict: `PASS_FAIL_CLOSED_COUNT6_DIRECT_OWNER_ONLY_PUBLIC_CONTRACT_MAX5`

A directly constructed actual-AEX `a9c0` owner vector can scan six entries and match index 5. This is deliberately not the public render contract: the AE parameter surface exposes only Color 0..4, its count slider is capped at `NUM_GAMMA_COLORS = 5`, and production clamps with `min(p.num_gamma_colors, NUM_GAMMA_COLORS)`.

Count 5 is therefore the maximum natural owner/classifier/worker/RenderBits path. Count 6 must not be implemented or claimed PF16/PF32/AE exact.
