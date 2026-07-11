# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_layer_straight_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 9241 | 251 | 0.980 | 0.023775 | 9086 | `[251, 251, 251, 2]` |
| olmdistancegradation_extended__case_0013 | 9006 | 2 | 0.008 | 0.005262 | 3612 | `[2, 2, 2, 2]` |
| olmdistancegradation_extended__case_0014 | 9630 | 4 | 0.016 | 0.005750 | 3826 | `[4, 4, 4, 2]` |
| olmdistancegradation_extended__case_0016 | 5373 | 2 | 0.008 | 0.003701 | 5373 | `[2, 2, 2, 0]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[985, 26]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[483, 510]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 0, 0, 64095]` delta=`[-251, 0, 0, 0]`
- `[1400, 190]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[1026, 232]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[1808, 376]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[887, 273]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`

## olmdistancegradation_extended__case_0013 Examples

- `[141, 1077]` source=`[16511, 16511, 16511, 32895]` candidate=`[16199, 16199, 16199, 32275]` reference=`[16199, 16199, 16199, 32273]` delta=`[0, 0, 0, 2]`
- `[1791, 226]` source=`[26777, 26777, 26777, 41891]` candidate=`[26271, 26271, 26271, 41101]` reference=`[26269, 26269, 26269, 41099]` delta=`[2, 2, 2, 2]`
- `[503, 227]` source=`[579, 579, 579, 6167]` candidate=`[567, 567, 567, 6051]` reference=`[567, 567, 567, 6049]` delta=`[0, 0, 0, 2]`
- `[387, 227]` source=`[18095, 18095, 18095, 34437]` candidate=`[17751, 17751, 17751, 33787]` reference=`[17753, 17753, 17753, 33787]` delta=`[-2, -2, -2, 0]`
- `[384, 227]` source=`[26777, 26777, 26777, 41891]` candidate=`[26271, 26271, 26271, 41101]` reference=`[26269, 26269, 26269, 41099]` delta=`[2, 2, 2, 2]`
- `[289, 227]` source=`[225, 225, 225, 3855]` candidate=`[219, 219, 219, 3783]` reference=`[221, 221, 221, 3781]` delta=`[-2, -2, -2, 2]`

## olmdistancegradation_extended__case_0014 Examples

- `[153, 160]` source=`[20035, 20035, 20035, 36237]` candidate=`[19985, 19985, 19985, 36151]` reference=`[19989, 19989, 19989, 36151]` delta=`[-4, -4, -4, 0]`
- `[752, 10]` source=`[20035, 20035, 20035, 36237]` candidate=`[19985, 19985, 19985, 36151]` reference=`[19989, 19989, 19989, 36151]` delta=`[-4, -4, -4, 0]`
- `[1902, 343]` source=`[20035, 20035, 20035, 36237]` candidate=`[19985, 19985, 19985, 36151]` reference=`[19989, 19989, 19989, 36151]` delta=`[-4, -4, -4, 0]`
- `[234, 1039]` source=`[20035, 20035, 20035, 36237]` candidate=`[19985, 19985, 19985, 36151]` reference=`[19989, 19989, 19989, 36151]` delta=`[-4, -4, -4, 0]`
- `[935, 277]` source=`[20035, 20035, 20035, 36237]` candidate=`[19985, 19985, 19985, 36151]` reference=`[19989, 19989, 19989, 36151]` delta=`[-4, -4, -4, 0]`
- `[351, 838]` source=`[20035, 0, 0, 36237]` candidate=`[19985, 0, 0, 36151]` reference=`[19989, 0, 0, 36151]` delta=`[-4, 0, 0, 0]`

## olmdistancegradation_extended__case_0016 Examples

- `[141, 1076]` source=`[6611, 6611, 6611, 20817]` candidate=`[6609, 6609, 6609, 20817]` reference=`[6611, 6611, 6611, 20817]` delta=`[-2, -2, -2, 0]`
- `[1348, 224]` source=`[14271, 14271, 14271, 30583]` candidate=`[14269, 14269, 14269, 30583]` reference=`[14271, 14271, 14271, 30583]` delta=`[-2, -2, -2, 0]`
- `[1867, 224]` source=`[32291, 32291, 32291, 46003]` candidate=`[32289, 32289, 32289, 46003]` reference=`[32291, 32291, 32291, 46003]` delta=`[-2, -2, -2, 0]`
- `[1892, 224]` source=`[47457, 47457, 47457, 55769]` candidate=`[47455, 47455, 47455, 55769]` reference=`[47457, 47457, 47457, 55769]` delta=`[-2, -2, -2, 0]`
- `[100, 225]` source=`[57085, 57085, 57085, 61165]` candidate=`[57083, 57083, 57083, 61165]` reference=`[57085, 57085, 57085, 61165]` delta=`[-2, -2, -2, 0]`
- `[101, 225]` source=`[3273, 3273, 3273, 14649]` candidate=`[3271, 3271, 3271, 14649]` reference=`[3273, 3273, 3273, 14649]` delta=`[-2, -2, -2, 0]`
