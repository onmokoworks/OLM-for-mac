# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca30_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 7709 | 14 | 0.055 | 0.008151 | 7554 | `[14, 14, 14, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[349, 948]` source=`[1095, 0, 0, 8481]` candidate=`[8397, 0, 0, 64997]` reference=`[8411, 0, 0, 64997]` delta=`[-14, 0, 0, 0]`
- `[264, 432]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[1864, 304]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[1500, 428]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[484, 243]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[1207, 520]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
