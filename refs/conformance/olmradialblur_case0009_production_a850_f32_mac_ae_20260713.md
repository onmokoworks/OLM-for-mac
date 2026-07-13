# OLMRadialBlur case0009 production A850 float32 Mac AE run

- Classification: `binary-grounded-known-red`
- Plug-in SHA-256: `58fddbca28fd7fa0b352365e1faba7b554bdf59e5c7ccf2cb6a6b1dac4c34059`
- Production raw A850: `32/32 exact`
- AEX-order candidate raw A850: `32/32 exact`
- Windows reference versus Mac AE: `max=1`, `12876` nonzero pixels, mean absolute sample diff `0.00000975317`

The actual-AEX per-operation float32 coordinate order is now the production Zoom 8bpc path. This closes the sampled raw A850 coordinate boundary, but it is not `AE exact`. The remaining case0009 work starts at semantic full-frame downstream index/cell/inverse-sampling host context. Reduced `32x32`, quality-step-90 cell evidence remains invalid for that comparison.
