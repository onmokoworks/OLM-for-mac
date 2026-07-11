# OLMDistanceGradation case_0023 Compose Witness - 2026-07-07

- Status: `compose-writeback-triplet-binary-grounded`
- Source: `tools/emulation/test_dg_compose.py`
- AEX: `aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex`
- Function: `DistanceGradation.aex FUN_181170480`
- Case: `olmdistancegradation_extended__case_0023`
- Promotion rule: `trunc(half_word / 32768.0 * 65535.0)`
- Safe claim: For the case_0023 threshold triplet, executing the Windows AEX compose/writeback callback locally maps injected field_x values to the recorded runtime RGBA16 words for this witness. The 2026-07-07 reference export audit supersedes treating those recorded words as the current PNG reference at every point, so this witness is a field-to-color mapping check, not current AE exact evidence.

## Leaf Check

- use_bg=1: got `[32768, 16384, 32768, 8192]` expected `[32768, 16384, 32768, 8192]` match `True`
- use_bg=0: got `[0, 0, 0, 0]` expected `[0, 0, 0, 0]` match `True`

## Triplet

| XY | field_x | raw AGRB | promoted RGBA16 | recorded RGBA16 | match |
| --- | ---: | --- | --- | --- | ---: |
| `(414,393)` | `0.0` | `[32768, 0, 3598, 30583]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `True` |
| `(415,393)` | `1.0` | `[32768, 0, 32768, 0]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |
| `(416,393)` | `1.0` | `[32768, 0, 32768, 0]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `True` |

## Limitations

- field_x values are injected from already-recorded threshold-side field witnesses; this does not re-prove field generation
- the recorded triplet words are not authoritative over the 2026-07-07 current Windows Software PNG recapture
- promotion rule is empirically grounded on this triplet, not all possible intermediate values
- 8bpc sibling and non-linear interpolation branches are not covered by this witness
- this is binary-grounded local emulation evidence, not Mac AE exact completion
