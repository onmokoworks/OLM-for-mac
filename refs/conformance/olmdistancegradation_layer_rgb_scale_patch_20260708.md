# OLMDistanceGradation Layer-source True16 Audit

- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Candidate root: `refs/reports/ae_single_case_olmdistancegradation_layer_rgb_scale_patch_20260708`

## Cases

| Case | nonzero_px | max true16 | max byte-equiv | mean true16 | same-alpha changed | channel max RGBA |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| olmdistancegradation_extended__case_0012 | 9241 | 251 | 0.980 | 0.023775 | 9086 | `[251, 251, 251, 2]` |
| olmdistancegradation_extended__case_0013 | 14221 | 9526 | 37.211 | 26.098239 | 8827 | `[9526, 9526, 9526, 2]` |
| olmdistancegradation_extended__case_0014 | 14618 | 9686 | 37.836 | 26.575019 | 8814 | `[9686, 9686, 9686, 2]` |

## Reading

The audited candidate must be treated as true 16-bit data. Pillow's default RGBA decode collapses these PNGs to 8-bit and hides the scale of this family.
The current case_0012 rerender shows a true16 max residual of 16384, which is the same as a byte-equivalent max of 64. This is a large Layer-source formula gap, not a one-word rounding issue.
Most changed pixels keep alpha unchanged while RGB is lower on the Mac candidate, so the active lane remains Layer/no-bg source RGB ownership or source-to-output-alpha scaling.

## olmdistancegradation_extended__case_0012 Examples

- `[985, 26]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[483, 510]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 0, 0, 64095]` delta=`[-251, 0, 0, 0]`
- `[1400, 190]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[1026, 232]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[1808, 376]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`
- `[887, 273]` source=`[0, 0, 0, 257]` candidate=`[0, 0, 0, 64095]` reference=`[251, 251, 251, 64095]` delta=`[-251, -251, -251, 0]`

## olmdistancegradation_extended__case_0013 Examples

- `[517, 89]` source=`[28783, 28783, 28783, 43433]` candidate=`[18715, 18715, 18715, 42613]` reference=`[28241, 28241, 28241, 42613]` delta=`[-9526, -9526, -9526, 0]`
- `[325, 788]` source=`[29125, 29125, 29125, 43689]` candidate=`[19049, 19049, 19049, 42865]` reference=`[28575, 28575, 28575, 42865]` delta=`[-9526, -9526, -9526, 0]`
- `[374, 313]` source=`[29125, 29125, 29125, 43689]` candidate=`[19049, 19049, 19049, 42865]` reference=`[28575, 28575, 28575, 42865]` delta=`[-9526, -9526, -9526, 0]`
- `[763, 409]` source=`[29125, 29125, 29125, 43689]` candidate=`[19049, 19049, 19049, 42865]` reference=`[28575, 28575, 28575, 42865]` delta=`[-9526, -9526, -9526, 0]`
- `[750, 78]` source=`[29125, 29125, 29125, 43689]` candidate=`[19049, 19049, 19049, 42865]` reference=`[28575, 28575, 28575, 42865]` delta=`[-9526, -9526, -9526, 0]`
- `[549, 211]` source=`[29469, 29469, 29469, 43947]` candidate=`[19387, 19387, 19387, 43117]` reference=`[28913, 28913, 28913, 43117]` delta=`[-9526, -9526, -9526, 0]`

## olmdistancegradation_extended__case_0014 Examples

- `[703, 234]` source=`[29125, 29125, 29125, 43689]` candidate=`[19369, 19369, 19369, 43585]` reference=`[29055, 29055, 29055, 43585]` delta=`[-9686, -9686, -9686, 0]`
- `[290, 226]` source=`[29469, 29469, 29469, 43947]` candidate=`[19713, 19713, 19713, 43843]` reference=`[29399, 29399, 29399, 43843]` delta=`[-9686, -9686, -9686, 0]`
- `[297, 376]` source=`[29469, 29469, 29469, 43947]` candidate=`[19713, 19713, 19713, 43843]` reference=`[29399, 29399, 29399, 43843]` delta=`[-9686, -9686, -9686, 0]`
- `[1310, 56]` source=`[29125, 29125, 29125, 43689]` candidate=`[19369, 19369, 19369, 43585]` reference=`[29055, 29055, 29055, 43585]` delta=`[-9686, -9686, -9686, 0]`
- `[1168, 140]` source=`[28783, 28783, 28783, 43433]` candidate=`[19029, 19029, 19029, 43331]` reference=`[28715, 28715, 28715, 43329]` delta=`[-9686, -9686, -9686, 2]`
- `[233, 839]` source=`[29469, 29469, 29469, 43947]` candidate=`[19713, 19713, 19713, 43843]` reference=`[29399, 29399, 29399, 43843]` delta=`[-9686, -9686, -9686, 0]`
