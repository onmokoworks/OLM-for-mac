# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca29_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 7831 | 16 | 0.062 | 0.008623 | 7676 | `[16, 16, 16, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[1747, 477]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[268, 251]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[1867, 226]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[670, 430]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[142, 232]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[36, 906]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
