# OLMDistanceGradation 0010/0011 AEX fieldgen probe - 2026-07-09

This runs the real Windows `DistanceGradation.aex` field-generation helper
under the local AEX CPU emulator with the validated OpenCV detours:
`threshold`, `dist_transform`, `resize_same_shape`, and `normalize_minmax`.

- Decision: `fieldgen-floats-match-current-mac-but-pack-rule-sign-flips`

## Samples

| Probe | XY | Field X | Field*32768 | Floor | Ceil | Windows-required field word | Match |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `case0010_inside` | `(901,394)` | 0.698593139648 | 22891.5 | 22891 | 22892 | 22892 | ceil |
| `case0010_outside` | `(6,40)` | 0.900283813477 | 29500.5 | 29500 | 29501 | 29500 | floor |
| `case0011_inside` | `(915,392)` | 0.134536772966 | 4408.50097656 | 4408 | 4409 | 4409 | ceil |

## Reading

- The AEX helper completes for the full `1920x1080` inputs and reaches the expected OpenCV detours in each run.
- The emitted float field values reproduce the current Mac-side field floats seen in earlier local probes.
- The Windows-required field-word relation is sign-flipped: the outside witness matches `floor`, while both inside witnesses require `ceil`.
- This rejects a single global final-writer rule and also rejects a simple one-rule PF16 field-pack toggle over the current field floats.
- The next proof is the field-world pack/consume boundary in the real Windows run, or a same-run true16 TIFF/EXR export only if export binding is still needed.
