# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca87_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 5345 | 9176 | 35.844 | 0.006523 | 5190 | `[4, 9176, 9176, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[400, 281]` source=`[3873, 1623, 1623, 15933]` candidate=`[15801, 15801, 15801, 64997]` reference=`[15801, 6625, 6625, 64997]` delta=`[0, 9176, 9176, 0]`
- `[16, 0]` source=`[11321, 11321, 11321, 27241]` candidate=`[27013, 27013, 27013, 64997]` reference=`[27017, 27017, 27017, 64997]` delta=`[-4, -4, -4, 0]`
- `[526, 490]` source=`[13095, 13095, 13095, 29297]` candidate=`[29051, 29051, 29051, 64997]` reference=`[29055, 29055, 29055, 64997]` delta=`[-4, -4, -4, 0]`
- `[392, 158]` source=`[11537, 11537, 11537, 27499]` candidate=`[27269, 27269, 27269, 64997]` reference=`[27273, 27273, 27273, 64997]` delta=`[-4, -4, -4, 0]`
- `[1074, 157]` source=`[11537, 11537, 11537, 27499]` candidate=`[27269, 27269, 27269, 64997]` reference=`[27273, 27273, 27273, 64997]` delta=`[-4, -4, -4, 0]`
- `[504, 493]` source=`[10483, 10483, 10483, 26213]` candidate=`[25993, 25993, 25993, 64997]` reference=`[25997, 25997, 25997, 64997]` delta=`[-4, -4, -4, 0]`
