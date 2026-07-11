# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_dominant180_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 1948 | 42676 | 166.703 | 0.016733 | 1793 | `[42676, 42676, 42676, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[1784, 632]` source=`[515, 515, 515, 43947]` candidate=`[43437, 43437, 43437, 64775]` reference=`[761, 761, 761, 64775]` delta=`[42676, 42676, 42676, 0]`
- `[75, 1063]` source=`[59511, 59511, 59511, 62451]` candidate=`[61723, 61723, 61723, 64775]` reference=`[61725, 61725, 61725, 64775]` delta=`[-2, -2, -2, 0]`
- `[1433, 241]` source=`[47457, 47457, 47457, 55769]` candidate=`[55309, 55309, 55309, 64997]` reference=`[55311, 55311, 55311, 64997]` delta=`[-2, -2, -2, 0]`
- `[1822, 238]` source=`[49667, 49667, 49667, 57053]` candidate=`[56389, 56389, 56389, 64775]` reference=`[56391, 56391, 56391, 64775]` delta=`[-2, -2, -2, 0]`
- `[1115, 239]` source=`[33017, 33017, 33017, 46517]` candidate=`[46133, 46133, 46133, 64997]` reference=`[46135, 46135, 46135, 64997]` delta=`[-2, -2, -2, 0]`
- `[1265, 239]` source=`[33017, 33017, 33017, 46517]` candidate=`[46133, 46133, 46133, 64997]` reference=`[46135, 46135, 46135, 64997]` delta=`[-2, -2, -2, 0]`
