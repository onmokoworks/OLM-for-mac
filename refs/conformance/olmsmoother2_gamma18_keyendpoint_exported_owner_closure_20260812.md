# OLMSmoother2 Gamma 1.8 + key endpoint owner closure

Verdict: `PASS_12_INTERMEDIATE_GAMMA_KEY_ENDPOINT_EXPORTED_OWNER_TO_PUBLIC_EFFECTMAIN_RAW_EXACT`

The pinned unchanged Windows AEX exported Smart owner and production public `EffectMain` SmartPreRender → SmartRender path agree on all 12 raw outputs: Version 1/2 × non-invert/invert × PF8/PF16/PF32. The fixed opaque 5x5 source retains 24 pixels from the earlier compound fixture and replaces pixel 0 with the exact `(202,187,230)` key endpoint; pixel 1 is the red Gamma endpoint. Gamma Colors is ordered `[red,key]` at the intermediate Gamma Value `1.8`, with Smoothness/Range/Extra Smooth all `100`.

As an observability control, the same actual Version 2 non-invert owner was also run at Gamma `1.0` and `2.4`; the `1.0`, `1.8`, and `2.4` raw hashes are pairwise distinct at every depth. Those endpoint controls are not added to the 12-cell actual-to-production claim.

A second same-source control changes only `Enable Color Key` from on to off. Its raw hash differs from the key-enabled Gamma 1.8 output at PF8, PF16, and PF32, making the exact key endpoint action output-observable without expanding the 12-cell exact claim.

The production public path additionally preserves complete input bytes, input/output row padding, pre-render rectangles, all parameter checkouts/checkins, and Smart lifecycle callbacks. No production code or installed plug-in was changed.

Boundary: Raw exact only for the fixed 5x5 opaque RGBA8 fixture (24 pixels retained from the prior compound fixture and pixel 0 replaced by the exact key endpoint), Color Key RGB=(202,187,230), Gamma Colors ordered [red,key], Gamma Value=1.8, Smoothness/Range/Extra Smooth=100, Version 1/2 x non-invert/invert x PF8/PF16/PF32. No arbitrary input, Gamma Value, key/palette, smoothing, geometry, AE-host, GPU, or installed-binary claim.
