# OLMBlur 16bpc Word-Delta Audit - 2026-06-28

## Summary

This audit re-reads the 16bpc PNGs through `refs/scripts/verify_manifest.py`
`png_rgba_array`, which uses ImageMagick `-depth 16 -endian MSB` when
available. Plain Pillow reads are not sufficient here because they collapse
the data to 8-bit values.

The current Mac AE 16bpc OLMBlur residual is mostly a one-word PF_Pixel16
difference:

- `case_0001..0006`: every nonzero exported PNG channel delta is `+2` or `-2`.
  In AE's 0..32768 16bpc word domain this is an inferred `+1` or `-1` word
  delta.
- All affected `case_0001..0006` exported values are odd on both sides. This is
  consistent with AE's 0..32768 internal 16bpc words being exported to 0..65535
  PNG space.
- `case_0007`: most residual pixels are the same inferred `+/-1` word family,
  but the localized `(0,0)` witness is separate: Windows reference
  `[0,0,0,65535]`, Mac candidate `[383,383,383,65535]`, i.e. roughly
  `-192` internal words on RGB.

This strengthens the existing rule: do not tune the blur kernel from this
evidence. The non-Legacy 16bpc problem is now narrowed to final float/helper
state or 16bpc writeback order at one-word precision. The Legacy case still has
a separate border/seed/all-same witness.

## Case Table

| Case | Class | Max exported delta | Nonzero px | Channel deltas | Inferred word deltas | Bounding box |
| --- | --- | ---: | ---: | --- | --- | --- |
| `case_0001` | `sign-mixed-one-word` | 2 | 66 | `{'-2': 14, '2': 52}` | `{'-1': 14, '1': 52}` | `[357, 169, 585, 396]` |
| `case_0002` | `sign-mixed-one-word` | 2 | 67 | `{'-2': 14, '2': 53}` | `{'-1': 14, '1': 53}` | `[379, 121, 606, 375]` |
| `case_0003` | `sign-mixed-one-word` | 2 | 414 | `{'-2': 189, '2': 225}` | `{'-1': 189, '1': 225}` | `[4, 0, 953, 539]` |
| `case_0004` | `sign-mixed-one-word` | 2 | 55 | `{'-2': 9, '2': 46}` | `{'-1': 9, '1': 46}` | `[348, 114, 611, 425]` |
| `case_0005` | `sign-mixed-one-word` | 2 | 106 | `{'-2': 54, '2': 112}` | `{'-1': 54, '1': 112}` | `[129, 8, 1903, 1062]` |
| `case_0006` | `sign-mixed-one-word` | 2 | 283 | `{'-2': 113, '2': 233}` | `{'-1': 113, '1': 233}` | `[29, 14, 1889, 1079]` |
| `case_0007` | `legacy-border-plus-one-word` | 383 | 304 | `{'-383': 3, '-2': 268, '2': 101}` | `{'-192': 3, '-1': 268, '1': 101}` | `[0, 0, 1859, 1060]` |

## Witnesses

- `case_0006 (314,14)`: Windows `[2201, 2201, 2201, 65535]`, Mac `[2199, 2199, 2199, 65535]`, delta `[2, 2, 2, 0]`, inferred words `[1, 1, 1]`.
- `case_0006 (29,71)`: Windows `[725, 725, 725, 65535]`, Mac `[727, 727, 727, 65535]`, delta `[-2, -2, -2, 0]`, inferred words `[-1, -1, -1]`.
- `case_0006 (694,137)`: Windows `[2361, 2361, 2361, 65535]`, Mac `[2363, 2363, 2363, 65535]`, delta `[-2, -2, -2, 0]`, inferred words `[-1, -1, -1]`.
- `case_0007 (0,0)`: Windows `[0, 0, 0, 65535]`, Mac `[383, 383, 383, 65535]`, delta `[-383, -383, -383, 0]`, inferred words `[-192, -192, -192]`.
- `case_0007 (951,7)`: Windows `[101, 101, 101, 65535]`, Mac `[103, 103, 103, 65535]`, delta `[-2, -2, -2, 0]`, inferred words `[-1, -1, -1]`.
- `case_0007 (1149,16)`: Windows `[5785, 5785, 5785, 65535]`, Mac `[5787, 5787, 5787, 65535]`, delta `[-2, -2, -2, 0]`, inferred words `[-1, -1, -1]`.

## Next Evidence

- For non-Legacy `case_0001..0006`, prove whether the one-word sign-mixed
  residual comes from final pre-writeback float state, the `+0.5` helper path,
  or an AE 16bpc store/export convention mismatch.
- For Legacy `case_0007`, keep the one-word family separate from the `(0,0)`
  border/seed/all-same state. Do not use the `(0,0)` witness to change the
  general non-Legacy writeback rule.
