# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca52_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 6741 | 6 | 0.023 | 0.005919 | 6586 | `[6, 6, 6, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[15, 0]` source=`[7451, 7451, 7451, 22101]` candidate=`[21913, 21913, 21913, 64997]` reference=`[21919, 21919, 21919, 64997]` delta=`[-6, -6, -6, 0]`
- `[1241, 131]` source=`[2829, 2829, 2829, 13621]` candidate=`[13503, 13503, 13503, 64997]` reference=`[13509, 13509, 13509, 64997]` delta=`[-6, -6, -6, 0]`
- `[1327, 162]` source=`[7451, 7451, 7451, 22101]` candidate=`[21913, 21913, 21913, 64997]` reference=`[21919, 21919, 21919, 64997]` delta=`[-6, -6, -6, 0]`
- `[1276, 405]` source=`[6129, 6129, 6129, 20045]` candidate=`[19873, 19873, 19873, 64997]` reference=`[19879, 19879, 19879, 64997]` delta=`[-6, -6, -6, 0]`
- `[1199, 161]` source=`[2829, 2829, 2829, 13621]` candidate=`[13503, 13503, 13503, 64997]` reference=`[13509, 13509, 13509, 64997]` delta=`[-6, -6, -6, 0]`
- `[1789, 407]` source=`[6129, 6129, 6129, 20045]` candidate=`[19873, 19873, 19873, 64997]` reference=`[19879, 19879, 19879, 64997]` delta=`[-6, -6, -6, 0]`
