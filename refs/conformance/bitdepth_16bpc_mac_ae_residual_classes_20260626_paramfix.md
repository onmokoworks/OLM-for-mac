# 16bpc Mac AE Residual Classes - 2026-06-26 Paramfix

Status: classified, not AE exact.

This classification uses the Mac AE rerun after `scripts/ae_pixel_validation_render.jsx` was fixed to replay manifest entries that provide `path` but not `path_full`.

| Label | Count |
| --- | ---: |
| full-scale-mismatch | 20 |
| large-structured-mismatch | 10 |

| Plugin slice | Residual labels |
| --- | --- |
| olmblur | full-scale-mismatch=5, large-structured-mismatch=2 |
| olmcolorkey | full-scale-mismatch=2 |
| olmdistancegradation_basic | full-scale-mismatch=5 |
| olmdistancegradation_blur | full-scale-mismatch=1 |
| olmdistancegradation_extended | full-scale-mismatch=7, large-structured-mismatch=8 |

| Feature flag | Failing cases |
| --- | ---: |
| `Power=1` | 17 |
| `olmdistancegradation_extended` | 15 |
| `Render Mode=1` | 13 |
| `In/Out=3` | 11 |
| `Interpolation Mode=2` | 11 |
| `Use Background Color=1` | 11 |
| `In/Out=1` | 10 |
| `Use Background Color=0` | 10 |
| `Render Mode=2` | 8 |
| `olmblur` | 7 |
| `Interpolation Mode=1` | 5 |
| `olmdistancegradation_basic` | 5 |
| `Interpolation Mode=4` | 3 |
| `Color Keep=0` | 2 |
| `Edge Blur=None` | 2 |
| `Edge Thin=None` | 2 |
| `Interpolation Mode=3` | 2 |
| `Power=2.59740734100342` | 2 |
| `Threshold=0` | 2 |
| `olmcolorkey` | 2 |

| Request | Case | Label | Max | Mean | Candidate 8bit score | Channel mean delta RGBA | Key params |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| bitdepth16_olmblur_exact | olmblur__case_0001 | full-scale-mismatch | 65023 | 0.0435 | 0.8825 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0002 | full-scale-mismatch | 65023 | 0.0437 | 0.8825 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0003 | large-structured-mismatch | 512 | 0.1022 | 0.6667 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0004 | large-structured-mismatch | 512 | 0.0094 | 0.8747 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0005 | full-scale-mismatch | 65023 | 0.0308 | 0.7816 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0006 | full-scale-mismatch | 65023 | 0.0788 | 0.4385 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0007 | full-scale-mismatch | 65023 | 0.0423 | 0.2569 | `[0, 0, 0, 0]` | `{}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0008 | full-scale-mismatch | 65535 | 0.5057 | 1.0000 | `[1, 0, 0, 1]` | `{"Color Keep": 0, "Color Space": 6, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 1, "Per Color": 0, "Premultiplied Color": 0, "Threshold": 0}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0009 | full-scale-mismatch | 65535 | 100.9161 | 1.0000 | `[2, 0, 3, 398]` | `{"Color Keep": 0, "Color Space": 3, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 3, "Per Color": 1, "Premultiplied Color": 0, "Threshold": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0002 | full-scale-mismatch | 65535 | 32767.5000 | 1.0000 | `[65535, 0, 0, 65535]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 128, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 128, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0015 | full-scale-mismatch | 65023 | 26.1004 | 0.9297 | `[40, 22, 22, 19]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 424, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0017 | full-scale-mismatch | 65023 | 121.0044 | 0.9572 | `[180, 129, 129, 47]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0018 | full-scale-mismatch | 65023 | 44.3194 | 0.9039 | `[68, 0, 109, 0]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0019 | full-scale-mismatch | 65023 | 53.9130 | 0.9041 | `[107, 0, 109, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_blur_exact | olmdistancegradation_blur__case_0029 | full-scale-mismatch | 65293 | 2232.4321 | 0.9115 | `[2659, 0, 3096, 3175]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 158, "Interpolation Mode": 1, "Invert": 1, "Outside Threshold": 13, "Power": 0.00999999977648, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0010 | large-structured-mismatch | 64516 | 59.1351 | 0.7868 | `[118, 0, 0, 118]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 63, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 82, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0011 | large-structured-mismatch | 64511 | 10.6010 | 0.8683 | `[21, 0, 0, 21]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 348, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 0, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0012 | large-structured-mismatch | 64516 | 148.8429 | 0.9453 | `[194, 141, 141, 119]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 122, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0013 | full-scale-mismatch | 65023 | 113.2652 | 0.9634 | `[167, 125, 125, 37]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 53, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0014 | full-scale-mismatch | 65023 | 118.9313 | 0.9282 | `[172, 142, 142, 21]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 424, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0016 | full-scale-mismatch | 65024 | 108.2735 | 0.9939 | `[153, 140, 140, 0]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 0, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0020 | large-structured-mismatch | 60910 | 14.4223 | 0.9954 | `[28, 0, 29, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0021 | large-structured-mismatch | 60910 | 14.4367 | 1.0000 | `[28, 0, 29, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 78, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 402, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0022 | large-structured-mismatch | 60910 | 134.6708 | 1.0000 | `[264, 0, 275, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 36, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 11, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0023 | large-structured-mismatch | 60910 | 19.9982 | 1.0000 | `[39, 0, 41, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 36, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 0, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0024 | full-scale-mismatch | 65023 | 151.6257 | 0.5912 | `[347, 0, 260, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 3, "Invert": 0, "Outside Threshold": 17, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0025 | full-scale-mismatch | 65023 | 208.5964 | 0.6430 | `[313, 0, 521, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 3, "Invert": 1, "Outside Threshold": 13, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0026 | large-structured-mismatch | 60619 | 7794.7190 | 0.8677 | `[15658, 0, 15521, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 2.59740734100342, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0027 | full-scale-mismatch | 65525 | 3631.3330 | 0.9461 | `[12872, 929, 724, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 2.59740734100342, "Render Mode": 2, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0028 | full-scale-mismatch | 65412 | 3657.1955 | 0.9897 | `[13163, 693, 773, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 0.40016460418701, "Render Mode": 2, "Use Background Color": 1}` |

Interpretation:
- `full-scale-mismatch` is too large to treat as rounding; inspect parameter replay/color management/effect path before tuning kernels.
- `candidate-close-to-input` suggests the effect path may not have applied or a controlling parameter was replayed incorrectly.
- `candidate-looks-8bit-quantized` suggests a bit-depth/writeback path issue.
