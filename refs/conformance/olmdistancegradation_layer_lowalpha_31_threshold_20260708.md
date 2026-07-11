# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_layer_lowalpha_31_threshold_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 9241 | 62 | 0.242 | 0.016957 | 9086 | `[62, 62, 62, 2]` |
| olmdistancegradation_extended__case_0013 | 9075 | 7 | 0.027 | 0.005379 | 3681 | `[7, 7, 7, 2]` |
| olmdistancegradation_extended__case_0014 | 9630 | 7 | 0.027 | 0.005868 | 3826 | `[7, 7, 7, 2]` |
| olmdistancegradation_extended__case_0016 | 5432 | 7 | 0.027 | 0.003856 | 5432 | `[7, 7, 7, 0]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[67, 376]` source=`[23, 23, 23, 1285]` candidate=`[1211, 1211, 1211, 64997]` reference=`[1273, 1273, 1273, 64997]` delta=`[-62, -62, -62, 0]`
- `[842, 12]` source=`[23, 23, 23, 1285]` candidate=`[1211, 1211, 1211, 64997]` reference=`[1273, 1273, 1273, 64997]` delta=`[-62, -62, -62, 0]`
- `[21, 807]` source=`[23, 23, 23, 1285]` candidate=`[1211, 1211, 1211, 64997]` reference=`[1273, 1273, 1273, 64997]` delta=`[-62, -62, -62, 0]`
- `[1791, 3]` source=`[23, 23, 23, 1285]` candidate=`[1211, 1211, 1211, 64997]` reference=`[1273, 1273, 1273, 64997]` delta=`[-62, -62, -62, 0]`
- `[280, 861]` source=`[23, 23, 23, 1285]` candidate=`[1211, 1211, 1211, 64997]` reference=`[1273, 1273, 1273, 64997]` delta=`[-62, -62, -62, 0]`
- `[528, 487]` source=`[23, 23, 23, 1285]` candidate=`[1211, 1211, 1211, 64997]` reference=`[1273, 1273, 1273, 64997]` delta=`[-62, -62, -62, 0]`

## olmdistancegradation_extended__case_0013 Examples

- `[606, 307]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 757]` reference=`[7, 7, 7, 755]` delta=`[-7, -7, -7, 2]`
- `[1726, 544]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 757]` reference=`[7, 7, 7, 755]` delta=`[-7, -7, -7, 2]`
- `[1133, 13]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 757]` reference=`[7, 7, 7, 755]` delta=`[-7, -7, -7, 2]`
- `[476, 437]` source=`[7, 0, 0, 771]` candidate=`[0, 0, 0, 757]` reference=`[7, 0, 0, 755]` delta=`[-7, 0, 0, 2]`
- `[1051, 271]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 757]` reference=`[7, 7, 7, 755]` delta=`[-7, -7, -7, 2]`
- `[956, 152]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 757]` reference=`[7, 7, 7, 755]` delta=`[-7, -7, -7, 2]`

## olmdistancegradation_extended__case_0014 Examples

- `[322, 166]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 769]` reference=`[7, 7, 7, 769]` delta=`[-7, -7, -7, 0]`
- `[198, 302]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 769]` reference=`[7, 7, 7, 769]` delta=`[-7, -7, -7, 0]`
- `[457, 310]` source=`[7, 0, 0, 771]` candidate=`[0, 0, 0, 769]` reference=`[7, 0, 0, 769]` delta=`[-7, 0, 0, 0]`
- `[255, 383]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 769]` reference=`[7, 7, 7, 769]` delta=`[-7, -7, -7, 0]`
- `[764, 408]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 769]` reference=`[7, 7, 7, 769]` delta=`[-7, -7, -7, 0]`
- `[279, 887]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 769]` reference=`[7, 7, 7, 769]` delta=`[-7, -7, -7, 0]`

## olmdistancegradation_extended__case_0016 Examples

- `[764, 408]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 771]` reference=`[7, 7, 7, 771]` delta=`[-7, -7, -7, 0]`
- `[328, 536]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 771]` reference=`[7, 7, 7, 771]` delta=`[-7, -7, -7, 0]`
- `[1135, 19]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 771]` reference=`[7, 7, 7, 771]` delta=`[-7, -7, -7, 0]`
- `[1917, 477]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 771]` reference=`[7, 7, 7, 771]` delta=`[-7, -7, -7, 0]`
- `[1097, 106]` source=`[7, 7, 7, 771]` candidate=`[0, 0, 0, 771]` reference=`[7, 7, 7, 771]` delta=`[-7, -7, -7, 0]`
- `[455, 301]` source=`[7, 0, 0, 771]` candidate=`[0, 0, 0, 771]` reference=`[7, 0, 0, 771]` delta=`[-7, 0, 0, 0]`
