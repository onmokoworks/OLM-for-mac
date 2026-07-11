# OLMDistanceGradation 0010/0011 field-pack/read audit - 2026-07-09

This is a local arithmetic audit, not an implementation change. It checks
whether the new Windows PF16 store words can be explained by simply packing
the current Mac float field into a PF16 field world before `FUN_181170480`
reads it.

- Decision: `field-pack-alone-insufficient-sign-flipped-boundary`

| Case | XY | Mac field*32768 | Required field word | Delta | floor | ceil | round-half-up |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `olmdistancegradation_extended__case_0010` | `(6,40)` | 29500.501953125 | 29500 | -0.501953125 | 3268* | 3267 | 3267 |
| `olmdistancegradation_extended__case_0010` | `(901,394)` | 22891.498046875 | 22892 | 0.501953125 | 9877 | 9876* | 9877 |
| `olmdistancegradation_extended__case_0011` | `(915,392)` | 4408.500976562 | 4409 | 0.499023438 | 28360 | 28359* | 28359* |

`*` marks a model that reproduces the Windows store word for that single witness.

## Reading

- Windows `FUN_181170480` reads a PF16 field-world word and multiplies by `1/32768`; the current Mac port reads `std::vector<float> df.x` directly.
- A PF16 field-world read is therefore a plausible missing boundary, but no single `floor`/`ceil`/`round` pack rule explains all sign-flipped witnesses.
- The remaining discriminator is a raw-distance / normalization-denominator / OpenCV field-pack boundary, not final `clamp16()` alone.
- Do not change global output rounding from this audit.
