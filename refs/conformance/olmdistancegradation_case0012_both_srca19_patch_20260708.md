# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca19_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 8324 | 24 | 0.094 | 0.010638 | 8169 | `[24, 24, 24, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[906, 186]` source=`[361, 361, 361, 4883]` candidate=`[4817, 4817, 4817, 64997]` reference=`[4841, 4841, 4841, 64997]` delta=`[-24, -24, -24, 0]`
- `[1701, 9]` source=`[361, 361, 361, 4883]` candidate=`[4817, 4817, 4817, 64997]` reference=`[4841, 4841, 4841, 64997]` delta=`[-24, -24, -24, 0]`
- `[1657, 420]` source=`[361, 361, 361, 4883]` candidate=`[4817, 4817, 4817, 64997]` reference=`[4841, 4841, 4841, 64997]` delta=`[-24, -24, -24, 0]`
- `[1590, 423]` source=`[361, 361, 361, 4883]` candidate=`[4817, 4817, 4817, 64997]` reference=`[4841, 4841, 4841, 64997]` delta=`[-24, -24, -24, 0]`
- `[583, 29]` source=`[361, 361, 361, 4883]` candidate=`[4817, 4817, 4817, 64997]` reference=`[4841, 4841, 4841, 64997]` delta=`[-24, -24, -24, 0]`
- `[1843, 483]` source=`[361, 361, 361, 4883]` candidate=`[4817, 4817, 4817, 64997]` reference=`[4841, 4841, 4841, 64997]` delta=`[-24, -24, -24, 0]`
