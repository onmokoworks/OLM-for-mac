# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca_all_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 31506 | 64744 | 252.906 | 180.012153 | 31351 | `[64744, 64744, 64744, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[625, 613]` source=`[0, 0, 257, 65535]` candidate=`[0, 0, 64997, 64997]` reference=`[0, 0, 253, 64997]` delta=`[0, 0, 64744, 0]`
- `[1044, 348]` source=`[257, 65535, 11051, 65535]` candidate=`[64997, 64997, 64997, 64997]` reference=`[253, 64997, 10959, 64997]` delta=`[64744, 0, 54038, 0]`
- `[778, 454]` source=`[65535, 257, 257, 65535]` candidate=`[64997, 64997, 64997, 64997]` reference=`[64997, 253, 253, 64997]` delta=`[0, 64744, 64744, 0]`
- `[337, 618]` source=`[257, 257, 65535, 65535]` candidate=`[64997, 64997, 64997, 64997]` reference=`[253, 253, 64997, 64997]` delta=`[64744, 64744, 0, 0]`
- `[627, 613]` source=`[0, 0, 257, 65535]` candidate=`[0, 0, 64997, 64997]` reference=`[0, 0, 253, 64997]` delta=`[0, 0, 64744, 0]`
- `[626, 613]` source=`[0, 0, 257, 65535]` candidate=`[0, 0, 64997, 64997]` reference=`[0, 0, 253, 64997]` delta=`[0, 0, 64744, 0]`
