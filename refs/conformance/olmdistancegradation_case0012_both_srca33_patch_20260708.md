# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca33_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 7643 | 14 | 0.055 | 0.008013 | 7488 | `[14, 14, 14, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[271, 201]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[352, 784]` source=`[1095, 0, 0, 8481]` candidate=`[8397, 0, 0, 64997]` reference=`[8411, 0, 0, 64997]` delta=`[-14, 0, 0, 0]`
- `[135, 1024]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[601, 151]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[484, 243]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
- `[1138, 72]` source=`[1095, 1095, 1095, 8481]` candidate=`[8397, 8397, 8397, 64997]` reference=`[8411, 8411, 8411, 64997]` delta=`[-14, -14, -14, 0]`
