# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca20_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 8224 | 20 | 0.078 | 0.009964 | 8069 | `[20, 20, 20, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[3, 487]` source=`[485, 485, 485, 5653]` candidate=`[5585, 5585, 5585, 64997]` reference=`[5605, 5605, 5605, 64997]` delta=`[-20, -20, -20, 0]`
- `[1617, 19]` source=`[485, 485, 485, 5653]` candidate=`[5585, 5585, 5585, 64997]` reference=`[5605, 5605, 5605, 64997]` delta=`[-20, -20, -20, 0]`
- `[1004, 110]` source=`[485, 485, 485, 5653]` candidate=`[5585, 5585, 5585, 64997]` reference=`[5605, 5605, 5605, 64997]` delta=`[-20, -20, -20, 0]`
- `[1645, 465]` source=`[485, 485, 485, 5653]` candidate=`[5585, 5585, 5585, 64997]` reference=`[5605, 5605, 5605, 64997]` delta=`[-20, -20, -20, 0]`
- `[366, 315]` source=`[485, 485, 485, 5653]` candidate=`[5585, 5585, 5585, 64997]` reference=`[5605, 5605, 5605, 64997]` delta=`[-20, -20, -20, 0]`
- `[485, 536]` source=`[485, 0, 0, 5653]` candidate=`[5585, 0, 0, 64997]` reference=`[5605, 0, 0, 64997]` delta=`[-20, 0, 0, 0]`
