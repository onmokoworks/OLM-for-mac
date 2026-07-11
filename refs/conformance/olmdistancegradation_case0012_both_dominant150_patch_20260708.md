# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_case0012_both_dominant150_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 2948 | 2 | 0.008 | 0.001990 | 2793 | `[2, 2, 2, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[268, 1069]` source=`[26447, 26447, 26447, 41633]` candidate=`[41289, 41289, 41289, 64997]` reference=`[41291, 41291, 41291, 64997]` delta=`[-2, -2, -2, 0]`
- `[445, 231]` source=`[30511, 30511, 30511, 44717]` candidate=`[44347, 44347, 44347, 64997]` reference=`[44349, 44349, 44349, 64997]` delta=`[-2, -2, -2, 0]`
- `[847, 233]` source=`[29469, 29469, 29469, 43947]` candidate=`[43583, 43583, 43583, 64997]` reference=`[43585, 43585, 43585, 64997]` delta=`[-2, -2, -2, 0]`
- `[340, 233]` source=`[32291, 32291, 32291, 46003]` candidate=`[45623, 45623, 45623, 64997]` reference=`[45625, 45625, 45625, 64997]` delta=`[-2, -2, -2, 0]`
- `[147, 233]` source=`[26447, 26447, 26447, 41633]` candidate=`[41289, 41289, 41289, 64997]` reference=`[41291, 41291, 41291, 64997]` delta=`[-2, -2, -2, 0]`
- `[1776, 232]` source=`[23283, 23283, 23283, 39063]` candidate=`[38739, 38739, 38739, 64997]` reference=`[38741, 38741, 38741, 64997]` delta=`[-2, -2, -2, 0]`
