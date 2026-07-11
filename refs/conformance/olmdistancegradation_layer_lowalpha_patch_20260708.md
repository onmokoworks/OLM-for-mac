# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_layer_lowalpha_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 9241 | 48 | 0.188 | 0.015321 | 9086 | `[48, 48, 48, 2]` |
| olmdistancegradation_extended__case_0013 | 9202 | 47 | 0.184 | 0.007656 | 3808 | `[47, 47, 47, 2]` |
| olmdistancegradation_extended__case_0014 | 9630 | 47 | 0.184 | 0.008145 | 3826 | `[47, 47, 47, 2]` |
| olmdistancegradation_extended__case_0016 | 5543 | 47 | 0.184 | 0.006208 | 5543 | `[47, 47, 47, 0]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
Use the `max true16` column for implementation work. The `max byte-equiv` column is included only to explain older reports that described true16 residuals after an 8-bit-style scale conversion.
If the high-delta examples preserve alpha while RGB is lower on the Mac candidate, the active lane is Layer/no-bg source RGB ownership or source-to-output-alpha scaling, not distance-field topology.

## olmdistancegradation_extended__case_0012 Examples

- `[106, 223]` source=`[79, 79, 79, 2313]` candidate=`[2245, 2245, 2245, 64997]` reference=`[2293, 2293, 2293, 64997]` delta=`[-48, -48, -48, 0]`
- `[488, 478]` source=`[79, 79, 79, 2313]` candidate=`[2245, 2245, 2245, 64997]` reference=`[2293, 2293, 2293, 64997]` delta=`[-48, -48, -48, 0]`
- `[1034, 4]` source=`[79, 79, 79, 2313]` candidate=`[2245, 2245, 2245, 64997]` reference=`[2293, 2293, 2293, 64997]` delta=`[-48, -48, -48, 0]`
- `[858, 129]` source=`[79, 79, 79, 2313]` candidate=`[2245, 2245, 2245, 64997]` reference=`[2293, 2293, 2293, 64997]` delta=`[-48, -48, -48, 0]`
- `[617, 554]` source=`[79, 79, 79, 2313]` candidate=`[2245, 2245, 2245, 64997]` reference=`[2293, 2293, 2293, 64997]` delta=`[-48, -48, -48, 0]`
- `[233, 590]` source=`[79, 79, 79, 2313]` candidate=`[2245, 2245, 2245, 64997]` reference=`[2293, 2293, 2293, 64997]` delta=`[-48, -48, -48, 0]`

## olmdistancegradation_extended__case_0013 Examples

- `[1521, 371]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1765]` reference=`[47, 47, 47, 1765]` delta=`[-47, -47, -47, 0]`
- `[382, 371]` source=`[47, 0, 0, 1799]` candidate=`[0, 0, 0, 1765]` reference=`[47, 0, 0, 1765]` delta=`[-47, 0, 0, 0]`
- `[1328, 528]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1765]` reference=`[47, 47, 47, 1765]` delta=`[-47, -47, -47, 0]`
- `[726, 301]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1765]` reference=`[47, 47, 47, 1765]` delta=`[-47, -47, -47, 0]`
- `[1173, 591]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1765]` reference=`[47, 47, 47, 1765]` delta=`[-47, -47, -47, 0]`
- `[1051, 268]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1765]` reference=`[47, 47, 47, 1765]` delta=`[-47, -47, -47, 0]`

## olmdistancegradation_extended__case_0014 Examples

- `[179, 19]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1795]` reference=`[47, 47, 47, 1793]` delta=`[-47, -47, -47, 2]`
- `[462, 336]` source=`[47, 0, 0, 1799]` candidate=`[0, 0, 0, 1795]` reference=`[47, 0, 0, 1793]` delta=`[-47, 0, 0, 2]`
- `[1180, 443]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1795]` reference=`[47, 47, 47, 1793]` delta=`[-47, -47, -47, 2]`
- `[1862, 289]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1795]` reference=`[47, 47, 47, 1793]` delta=`[-47, -47, -47, 2]`
- `[1239, 111]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1795]` reference=`[47, 47, 47, 1793]` delta=`[-47, -47, -47, 2]`
- `[414, 247]` source=`[47, 0, 0, 1799]` candidate=`[0, 0, 0, 1795]` reference=`[47, 0, 0, 1793]` delta=`[-47, 0, 0, 2]`

## olmdistancegradation_extended__case_0016 Examples

- `[1209, 527]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1799]` reference=`[47, 47, 47, 1799]` delta=`[-47, -47, -47, 0]`
- `[1147, 325]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1799]` reference=`[47, 47, 47, 1799]` delta=`[-47, -47, -47, 0]`
- `[908, 148]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1799]` reference=`[47, 47, 47, 1799]` delta=`[-47, -47, -47, 0]`
- `[931, 65]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1799]` reference=`[47, 47, 47, 1799]` delta=`[-47, -47, -47, 0]`
- `[329, 525]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1799]` reference=`[47, 47, 47, 1799]` delta=`[-47, -47, -47, 0]`
- `[280, 863]` source=`[47, 47, 47, 1799]` candidate=`[0, 0, 0, 1799]` reference=`[47, 47, 47, 1799]` delta=`[-47, -47, -47, 0]`
