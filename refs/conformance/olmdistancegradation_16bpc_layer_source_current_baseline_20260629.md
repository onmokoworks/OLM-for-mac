# OLMDistanceGradation 16bpc Layer/no-bg Current Baseline

- Date: `2026-06-29`
- Request dir: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- Purpose: freeze the current Mac-side post-fix witness values before the next Windows runtime-trace return is interpreted.

## Reading

- `case_0012` / `case_0016` are the active Layer/no-bg source-ownership family.
- `case_0020` / `case_0022` are control families showing the Constant boundary lane after the Constant-specific binary fix.
- Treat this file as the Mac-side baseline to compare against the pending Windows source-ownership runtime trace, not as completion evidence.

## Cases

### olmdistancegradation_extended__case_0012

- Family: `layer-no-bg-source-or-alpha-ownership`
- Candidate: `refs/reports/ae_single_case_olmdistancegradation_case0012_layer_no_bg_source_fix_installed_20260629/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0012.png`
- max: `16476`
- mean: `332.83683244116514`
- nonzero_px: `285406`
- bbox: `[0, 0, 1919, 1079]`
- max witness: `{'x': 427, 'y': 572, 'channel': 0, 'reference': [32859, 0, 0, 32859], 'candidate': [16383, 0, 0, 32767], 'delta': [-16476, 0, 0, -92]}`
- params: `{'Invert': 0, 'In/Out': 3, 'Inside Threshold': 122, 'Outside Threshold': 204, 'Render Mode': 2, 'Use Background Color': 0, 'Gradation Color': [1, 0, 0, 1], 'BG Color ': [0, 0, 0, 1], 'Interpolation Mode': 2, 'Power': 1, 'Blur Mode': 1, 'Blur Size': 0, 'Effect Opacity': 100, 'GPU Rendering': 1}`
- Primary Layer/no-bg ownership witness after the narrow straight-source-times-output-alpha patch.
- Windows runtime trace for source ownership should be judged against this current Mac post-fix baseline, not against the reverted or rejected unpremultiply variants.

| Point | input | reference | candidate | delta |
| --- | --- | --- | --- | --- |
| `(462,7)` | `[16255, 16255, 16255, 32639]` | `[32371, 32371, 32371, 64997]` | `[32105, 32105, 32105, 64997]` | `[-266, -266, -266, 0]` |
| `(72,8)` | `[16255, 16255, 16255, 32639]` | `[32371, 32371, 32371, 64997]` | `[32105, 32105, 32105, 64997]` | `[-266, -266, -266, 0]` |
| `(106,19)` | `[29125, 29125, 29125, 43689]` | `[43329, 43329, 43329, 64997]` | `[42975, 42975, 42975, 64997]` | `[-354, -354, -354, 0]` |
| `(0,0)` | `[0, 0, 0, 0]` | `[0, 0, 0, 43949]` | `[0, 0, 0, 43949]` | `[0, 0, 0, 0]` |

### olmdistancegradation_extended__case_0016

- Family: `layer-no-bg-source-or-alpha-ownership`
- Candidate: `refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/olmdistancegradation_extended__case_0016_rerun/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0016.png`
- max: `9710`
- mean: `26.64569022472994`
- nonzero_px: `14196`
- bbox: `[0, 0, 1919, 1079]`
- max witness: `{'x': 106, 'y': 19, 'channel': 0, 'reference': [29125, 29125, 29125, 43689], 'candidate': [19415, 19415, 19415, 43689], 'delta': [-9710, -9710, -9710, 0]}`
- params: `{'Invert': 1, 'In/Out': 1, 'Inside Threshold': 0, 'Outside Threshold': 204, 'Render Mode': 2, 'Use Background Color': 0, 'Gradation Color': [1, 0, 0, 1], 'BG Color ': [0, 0, 0, 1], 'Interpolation Mode': 2, 'Power': 1, 'Blur Mode': 1, 'Blur Size': 0, 'Effect Opacity': 100, 'GPU Rendering': 1}`
- Secondary Layer/no-bg family under Invert=1.
- Useful to confirm whether the same ownership rule explains both the primary and inverted residual family.

| Point | input | reference | candidate | delta |
| --- | --- | --- | --- | --- |
| `(15,0)` | `[7451, 7451, 7451, 22101]` | `[7451, 7451, 7451, 22101]` | `[2511, 2511, 2511, 22101]` | `[-4940, -4940, -4940, 0]` |
| `(106,19)` | `[29125, 29125, 29125, 43689]` | `[29125, 29125, 29125, 43689]` | `[19415, 19415, 19415, 43689]` | `[-9710, -9710, -9710, 0]` |
| `(447,0)` | `[15247, 15247, 15247, 31611]` | `[15247, 15247, 15247, 31611]` | `[7353, 7353, 7353, 31611]` | `[-7894, -7894, -7894, 0]` |
| `(0,0)` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` |

### olmdistancegradation_extended__case_0020

- Family: `constant-bg-binary-boundary`
- Candidate: `refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/olmdistancegradation_extended__case_0020/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0020.png`
- max: `61165`
- mean: `0.014407913773148148`
- nonzero_px: `1`
- bbox: `[434, 676, 434, 676]`
- max witness: `{'x': 434, 'y': 676, 'channel': 2, 'reference': [7195, 0, 61165, 65535], 'candidate': [65535, 0, 0, 65535], 'delta': [58340, 0, -61165, 0]}`
- params: `{'Invert': 0, 'In/Out': 1, 'Inside Threshold': 78, 'Outside Threshold': 204, 'Render Mode': 1, 'Use Background Color': 1, 'Gradation Color': [0.1098041459918, 0, 0.93333333730698, 1], 'BG Color ': [1, 0, 0, 1], 'Interpolation Mode': 1, 'Power': 1, 'Blur Mode': 1, 'Blur Size': 0, 'Effect Opacity': 100, 'GPU Rendering': 1}`
- Control family after the Constant-specific THRESH_BINARY fix.
- This is intentionally not the active runtime-trace target, but it is the best control that the Layer/no-bg patch did not regress the Constant boundary family.

| Point | input | reference | candidate | delta |
| --- | --- | --- | --- | --- |
| `(951,417)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(950,417)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(951,416)` | `[65535, 0, 0, 65535]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(0,0)` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` | `[0, 0, 0, 0]` |

### olmdistancegradation_extended__case_0022

- Family: `constant-bg-binary-boundary`
- Candidate: `refs/reports/ae_single_case_olmdistancegradation_probe_set_20260629/olmdistancegradation_extended__case_0022/olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0022.png`
- max: `61165`
- mean: `2.7663194444444446`
- nonzero_px: `192`
- bbox: `[70, 55, 1847, 891]`
- max witness: `{'x': 1101, 'y': 55, 'channel': 2, 'reference': [65535, 0, 0, 65535], 'candidate': [7195, 0, 61165, 65535], 'delta': [-58340, 0, 61165, 0]}`
- params: `{'Invert': 0, 'In/Out': 3, 'Inside Threshold': 36, 'Outside Threshold': 11, 'Render Mode': 1, 'Use Background Color': 1, 'Gradation Color': [0.1098041459918, 0, 0.93333333730698, 1], 'BG Color ': [1, 0, 0, 1], 'Interpolation Mode': 1, 'Power': 1, 'Blur Mode': 1, 'Blur Size': 0, 'Effect Opacity': 100, 'GPU Rendering': 1}`
- Boundary-localized Constant family after the Constant-specific THRESH_BINARY fix.
- Useful to keep the Constant lane separated from the Layer/no-bg ownership lane while Windows runtime evidence is pending.

| Point | input | reference | candidate | delta |
| --- | --- | --- | --- | --- |
| `(4,0)` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(28,0)` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(27,0)` | `[0, 0, 0, 0]` | `[7195, 0, 61165, 65535]` | `[7195, 0, 61165, 65535]` | `[0, 0, 0, 0]` |
| `(0,0)` | `[0, 0, 0, 0]` | `[65535, 0, 0, 65535]` | `[65535, 0, 0, 65535]` | `[0, 0, 0, 0]` |

## Next Evidence Boundary

- The pending Windows runtime trace should explain whether Layer/no-bg RGB ownership uses straight source RGB times output alpha, another source ownership rule, or an additional quantization step.
- If the returned Windows compose-path source values align with the `case_0012/0016` current Mac samples up to the remaining `-1/-2` RGB family, the next Mac work is likely quantization/rounding cleanup rather than another broad ownership rewrite.
- If they contradict these current samples, update the IR and keep the Constant control families separate from the Layer/no-bg lane.
