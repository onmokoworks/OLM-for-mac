# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_depthgate_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 278028 | 16384 | 64.000 | 332.197517 | 277873 | `[16384, 16384, 16384, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[415, 723]` source=`[65535, 0, 0, 65535]` candidate=`[16379, 0, 0, 32763]` reference=`[32763, 0, 0, 32763]` delta=`[-16384, 0, 0, 0]`
- `[1433, 572]` source=`[0, 65535, 10793, 65535]` candidate=`[0, 16519, 2719, 32903]` reference=`[0, 32903, 5417, 32903]` delta=`[0, -16384, -2698, 0]`
- `[1415, 627]` source=`[65535, 0, 0, 65535]` candidate=`[16103, 0, 0, 32487]` reference=`[32487, 0, 0, 32487]` delta=`[-16384, 0, 0, 0]`
- `[1409, 654]` source=`[65535, 0, 0, 65535]` candidate=`[16133, 0, 0, 32517]` reference=`[32517, 0, 0, 32517]` delta=`[-16384, 0, 0, 0]`
- `[823, 513]` source=`[65535, 0, 0, 65535]` candidate=`[16055, 0, 0, 32439]` reference=`[32439, 0, 0, 32439]` delta=`[-16384, 0, 0, 0]`
- `[822, 513]` source=`[65535, 0, 0, 65535]` candidate=`[16577, 0, 0, 32961]` reference=`[32961, 0, 0, 32961]` delta=`[-16384, 0, 0, 0]`
