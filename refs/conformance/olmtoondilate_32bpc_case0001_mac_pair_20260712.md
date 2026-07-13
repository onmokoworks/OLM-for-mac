# OLMToonDilate 32bpc case_0001 Mac effect/control pair (2026-07-12)

## FACT

- Mac host: After Effects `26.3x87`, `32bpc`, working space `None`, linear
  blending `false`, output template `OLM EXR 32 Float`.
- Bound plug-in SHA-256:
  `d47a81bd8259bd5ca0db31b71a4e0ffd4fef1c037ef31ffd1a922de1775954de`.
- Effect-on EXR SHA-256:
  `e6084b919345196020a2d30f95733f50eeb3e616b801770b4ec571c526577029`.
- No-effect EXR SHA-256:
  `9aa6b0f651764846f4b1267b845665c87d176aacca7727d2bffa29585cf1e85b`.
- Decoded raw float-bit diagnostics:
  - Mac no-effect vs Mac effect-on: `mismatched_samples=0`.
  - Windows before-effect vs Mac no-effect:
    `mismatched_samples=6220800`, `max_raw_u32_delta=36716840`.
  - Windows effect-on vs Mac effect-on:
    `mismatched_samples=6220800`, `max_raw_u32_delta=36716840`.
- This is exactly the same host-control residual count and maximum raw delta
  independently observed for ColorKey case_0002.

## CLASSIFICATION

`blocked-by-host-input-conversion`. The repaired plug-in loads and renders, and
this declared case is a Mac-side raw-float no-op. The cross-host difference is
already present in the control world and cannot be attributed to ToonDilate.
Require a same-contract Windows no-effect FLOAT EXR and complete host/template
binding before any 32bpc conformance promotion or kernel change.
