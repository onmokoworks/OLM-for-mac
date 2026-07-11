# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_srca43_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 7165 | 10 | 0.039 | 0.006878 | 7010 | `[10, 10, 10, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[450, 247]` source=`[1861, 1861, 1861, 11051]` candidate=`[10949, 10949, 10949, 64997]` reference=`[10959, 10959, 10959, 64997]` delta=`[-10, -10, -10, 0]`
- `[1693, 220]` source=`[1861, 1861, 1861, 11051]` candidate=`[10949, 10949, 10949, 64997]` reference=`[10959, 10959, 10959, 64997]` delta=`[-10, -10, -10, 0]`
- `[979, 17]` source=`[1861, 1861, 1861, 11051]` candidate=`[10949, 10949, 10949, 64997]` reference=`[10959, 10959, 10959, 64997]` delta=`[-10, -10, -10, 0]`
- `[1532, 46]` source=`[1861, 1861, 1861, 11051]` candidate=`[10949, 10949, 10949, 64997]` reference=`[10959, 10959, 10959, 64997]` delta=`[-10, -10, -10, 0]`
- `[1512, 447]` source=`[1861, 1861, 1861, 11051]` candidate=`[10949, 10949, 10949, 64997]` reference=`[10959, 10959, 10959, 64997]` delta=`[-10, -10, -10, 0]`
- `[377, 222]` source=`[1861, 1861, 1861, 11051]` candidate=`[10949, 10949, 10949, 64997]` reference=`[10959, 10959, 10959, 64997]` delta=`[-10, -10, -10, 0]`
