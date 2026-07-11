# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca51_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 6858 | 8 | 0.031 | 0.006203 | 6703 | `[8, 8, 8, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[1810, 599]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[470, 378]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[1220, 40]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[1161, 200]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[1298, 589]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[1309, 58]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
