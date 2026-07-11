# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca22_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 8118 | 16 | 0.062 | 0.009457 | 7963 | `[16, 16, 16, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[141, 268]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[155, 1059]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[230, 993]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[24, 399]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[1165, 310]` source=`[845, 845, 845, 7453]` candidate=`[7375, 7375, 7375, 64997]` reference=`[7391, 7391, 7391, 64997]` delta=`[-16, -16, -16, 0]`
- `[353, 752]` source=`[845, 0, 0, 7453]` candidate=`[7375, 0, 0, 64997]` reference=`[7391, 0, 0, 64997]` delta=`[-16, 0, 0, 0]`
