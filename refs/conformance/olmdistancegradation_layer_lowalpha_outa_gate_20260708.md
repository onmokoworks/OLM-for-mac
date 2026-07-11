# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_layer_lowalpha_outa_gate_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 9241 | 62 | 0.242 | 0.016957 | 9086 | `[62, 62, 62, 2]` |
| olmdistancegradation_extended__case_0013 | 9071 | 257 | 1.004 | 0.010746 | 3677 | `[257, 257, 257, 2]` |
| olmdistancegradation_extended__case_0014 | 9695 | 257 | 1.004 | 0.011235 | 3891 | `[257, 257, 257, 2]` |
| olmdistancegradation_extended__case_0016 | 5373 | 2 | 0.008 | 0.003701 | 5373 | `[2, 2, 2, 0]` |

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

- `[107, 885]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[887, 273]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[170, 238]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[316, 449]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[864, 130]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[1808, 376]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`

## olmdistancegradation_extended__case_0014 Examples

- `[481, 487]` source=`[0, 0, 0, 257]` candidate=`[257, 0, 0, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 0, 0, 0]`
- `[472, 403]` source=`[0, 0, 0, 257]` candidate=`[257, 0, 0, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 0, 0, 0]`
- `[467, 150]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[75, 250]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[887, 273]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`
- `[154, 368]` source=`[0, 0, 0, 257]` candidate=`[257, 257, 257, 257]` reference=`[0, 0, 0, 257]` delta=`[257, 257, 257, 0]`

## olmdistancegradation_extended__case_0016 Examples

- `[141, 1076]` source=`[6611, 6611, 6611, 20817]` candidate=`[6609, 6609, 6609, 20817]` reference=`[6611, 6611, 6611, 20817]` delta=`[-2, -2, -2, 0]`
- `[1348, 224]` source=`[14271, 14271, 14271, 30583]` candidate=`[14269, 14269, 14269, 30583]` reference=`[14271, 14271, 14271, 30583]` delta=`[-2, -2, -2, 0]`
- `[1867, 224]` source=`[32291, 32291, 32291, 46003]` candidate=`[32289, 32289, 32289, 46003]` reference=`[32291, 32291, 32291, 46003]` delta=`[-2, -2, -2, 0]`
- `[1892, 224]` source=`[47457, 47457, 47457, 55769]` candidate=`[47455, 47455, 47455, 55769]` reference=`[47457, 47457, 47457, 55769]` delta=`[-2, -2, -2, 0]`
- `[100, 225]` source=`[57085, 57085, 57085, 61165]` candidate=`[57083, 57083, 57083, 61165]` reference=`[57085, 57085, 57085, 61165]` delta=`[-2, -2, -2, 0]`
- `[101, 225]` source=`[3273, 3273, 3273, 14649]` candidate=`[3271, 3271, 3271, 14649]` reference=`[3273, 3273, 3273, 14649]` delta=`[-2, -2, -2, 0]`
