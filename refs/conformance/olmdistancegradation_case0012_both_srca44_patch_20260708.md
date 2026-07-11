# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca44_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 7067 | 8 | 0.031 | 0.006596 | 6912 | `[8, 8, 8, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[91, 95]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[1298, 589]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[705, 393]` source=`[2517, 2517, 2517, 12849]` candidate=`[12735, 12735, 12735, 64997]` reference=`[12743, 12743, 12743, 64997]` delta=`[-8, -8, -8, 0]`
- `[1334, 114]` source=`[2517, 2517, 2517, 12849]` candidate=`[12735, 12735, 12735, 64997]` reference=`[12743, 12743, 12743, 64997]` delta=`[-8, -8, -8, 0]`
- `[642, 507]` source=`[2619, 2619, 2619, 13107]` candidate=`[12991, 12991, 12991, 64997]` reference=`[12999, 12999, 12999, 64997]` delta=`[-8, -8, -8, 0]`
- `[807, 168]` source=`[2517, 2517, 2517, 12849]` candidate=`[12735, 12735, 12735, 64997]` reference=`[12743, 12743, 12743, 64997]` delta=`[-8, -8, -8, 0]`
