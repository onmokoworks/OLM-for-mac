# OLMDistanceGradation 0010/0011 normalization denominator audit - 2026-07-09

This audit quantifies how far the current Mac raw distance or normalization
denominator must move to reproduce the Windows-required PF16 field words.
It is not an implementation patch.

- Decision: `mixed-actual-max-and-threshold-half-boundary`

| Case | XY | Mode | Denom kind | Mac denom | Required denom | Denom delta | Raw delta if denom fixed |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `olmdistancegradation_extended__case_0010` | `(6,40)` | outside | actual_raw_max | 45.5411912019 | 45.5419661017 | 0.000774899770853 | -0.000697617896734 |
| `olmdistancegradation_extended__case_0010` | `(901,394)` | inside | ui_threshold | 62.9999999147 | 62.998618513 | -0.00138140166138 | 0.000965058802251 |
| `olmdistancegradation_extended__case_0011` | `(915,392)` | inside | ui_threshold | 348.000007975 | 347.960620322 | -0.039387652581 | 0.00529968750701 |

## Reading

- `(6,40)` is not threshold-normalized by `82`; it is normalized by the outside field's actual max (`~45.54119`).
- `(901,394)` and `(915,392)` are threshold-limited inside-field witnesses.
- All three are half-boundary scale problems, but they are not a single global denominator constant.
- The next local proof should inspect the AEX/OpenCV field preparation path that produces the stored field world: actual max measurement, threshold clamp precision, and PF16 field-world packing.
- Do not change final output rounding from this audit.
