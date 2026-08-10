# OLM RadialBlur PF32 Zoom Noise and Inner boundary — 2026-08-11

Status: **noise_and_inner_exact**

Type-1 Noise 25/100, Inner Strength 50/100, and all four cross-product cells match actual AEX from pre/post polar planes through padded production output. Noise first materializes the source span; both radial directions then consume the same span and accumulate in source order before one normalization pass. Radius cell zero remains the unblurred center sample. NV50 remains fail-closed.
