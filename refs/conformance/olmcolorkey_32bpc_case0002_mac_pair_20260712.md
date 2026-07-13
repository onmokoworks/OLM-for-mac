# OLMColorKey 32bpc case_0002 Mac effect/control pair (2026-07-12)

## FACT

- Mac host: After Effects `26.3x87`, project `32bpc`, working space `None`,
  linear blending `false`, output template `OLM EXR 32 Float`.
- Installed ColorKey binary SHA-256:
  `c3026c5facbdf227bec55c24e7257f0f94db5ddf94ce26cfb5b593681b5ed0ae`.
- The repaired OutFlags2 plug-in adds and renders without a declaration dialog.
- Mac no-effect FLOAT EXR SHA-256:
  `5d5474d599b527e165f28c5bf166f5b699e3d621ed2a08f6ecc76b0f7573db0d`.
- Mac effect-on FLOAT EXR SHA-256:
  `34e793358a23d755f4d0cf354f1a14f22702a5568c2043df89a8fc52e215f0ab`.
  The container hashes differ, but decoded channel sample bits are identical.
- Both Mac artifacts are uncompressed 1920x1080 four-channel FLOAT EXRs.
- Raw float-bit diagnostics:
  - Mac no-effect vs Mac effect-on: `mismatched_samples=0`.
  - Windows before-effect vs Mac no-effect:
    `mismatched_samples=6220800`, `max_raw_u32_delta=36716840`.
  - Windows effect-on vs Mac effect-on:
    `mismatched_samples=6220800`, `max_raw_u32_delta=36716840`.
- No NaN samples participate in these comparisons.

## CLASSIFICATION

`blocked-by-host-input-conversion`. Case_0002 is a Mac-side bit-exact no-op,
but the cross-host input/control worlds are already different before the
effect delta is attributable. This is not an OLMColorKey pixel failure and is
not 32bpc AE exact evidence. Do not tune ColorKey from this residual. The next
acceptable Windows return must bind a same-contract Windows no-effect FLOAT
EXR (or otherwise prove that the supplied before-effect artifact is the exact
post-import/render-queue control world) together with AE build, color settings,
linear-light off, template, and loaded AEX hash.

## RUNNER NOTE

The paired runner now sets `OLM_AE_FORCE_NEW_PROJECT=1` for both effect and
control artifacts. Its smoke covers the fresh-project environment contract.

## Rejected original-PNG candidate (2026-07-13)

`refs/win_references/20260604_olm/OLMColorKey/case_0002_before_effects.png`
(SHA-256 `7e3527fd86e6dc58ceb3477a4fb86b7d25d27c70060359d6b9c08a70eba075c4`)
was tested as a possible original source. A clean Mac AE26.3 effect/control
pair remained a Mac-side no-op, but Windows-before vs Mac-control increased to
`8049331` mismatched samples with maximum raw delta `1065353216`. Therefore
the old same-numbered PNG is not proven to be the 20260710 32bpc source asset
and is rejected as conformance input. Case numbering/source labels alone are
not provenance. Use the symmetric supplied-EXR re-import request instead.
