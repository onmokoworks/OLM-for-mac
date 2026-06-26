# 16bpc Mac AE Residual Classes - 2026-06-26

Status: classified, not AE exact.

| Label | Count |
| --- | ---: |
| candidate-looks-8bit-quantized | 4 |
| full-scale-mismatch | 29 |

| Plugin slice | Residual labels |
| --- | --- |
| olmblur | candidate-looks-8bit-quantized=4, full-scale-mismatch=3 |
| olmcolorkey | full-scale-mismatch=6 |
| olmdistancegradation_basic | full-scale-mismatch=4 |
| olmdistancegradation_blur | full-scale-mismatch=1 |
| olmdistancegradation_extended | full-scale-mismatch=15 |

| Feature flag | Failing cases |
| --- | ---: |
| `Power=1` | 16 |
| `olmdistancegradation_extended` | 15 |
| `Render Mode=1` | 12 |
| `In/Out=3` | 11 |
| `Use Background Color=1` | 11 |
| `Interpolation Mode=2` | 10 |
| `In/Out=1` | 9 |
| `Use Background Color=0` | 9 |
| `Render Mode=2` | 8 |
| `olmblur` | 7 |
| `Edge Blur=None` | 6 |
| `Edge Thin=None` | 6 |
| `olmcolorkey` | 6 |
| `Force Lower Precision=1` | 5 |
| `Interpolation Mode=1` | 5 |
| `olmdistancegradation_basic` | 4 |
| `Color Keep=0` | 3 |
| `Color Keep=1` | 3 |
| `Color Space=1` | 3 |
| `Interpolation Mode=4` | 3 |
| `Threshold=0` | 3 |
| `Interpolation Mode=3` | 2 |
| `Power=2.59740734100342` | 2 |
| `Threshold=1` | 2 |

| Request | Case | Label | Max | Mean | Candidate 8bit score | Channel mean delta RGBA | Key params |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| bitdepth16_olmblur_exact | olmblur__case_0001 | candidate-looks-8bit-quantized | 36812 | 650.6018 | 0.9969 | `[9992, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0002 | candidate-looks-8bit-quantized | 36812 | 650.6018 | 0.9969 | `[9992, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0003 | candidate-looks-8bit-quantized | 59796 | 2253.0972 | 0.9969 | `[23180, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0004 | candidate-looks-8bit-quantized | 36904 | 658.5122 | 0.9969 | `[10266, 0, 0, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0005 | full-scale-mismatch | 27142 | 236.1553 | 0.9091 | `[4679, 4167, 4336, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0006 | full-scale-mismatch | 49898 | 552.0764 | 0.9091 | `[13127, 12016, 12341, 0]` | `{}` |
| bitdepth16_olmblur_exact | olmblur__case_0007 | full-scale-mismatch | 56742 | 703.4014 | 0.9091 | `[18959, 17616, 17992, 0]` | `{}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0001 | full-scale-mismatch | 65535 | 3653.7734 | 1.0000 | `[6599, 129, 560, 7325]` | `{"Color Keep": 0, "Color Space": 1, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 1, "Per Color": 0, "Premultiplied Color": 0, "Threshold": 0.62000000476837}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0003 | full-scale-mismatch | 65535 | 18485.6960 | 1.0000 | `[6971, 501, 932, 65535]` | `{"Color Keep": 1, "Color Space": 1, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 1, "Per Color": 0, "Premultiplied Color": 0, "Threshold": 0}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0004 | full-scale-mismatch | 65535 | 14447.4319 | 1.0000 | `[0, 0, 0, 57790]` | `{"Color Keep": 1, "Color Space": 1, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 1, "Per Color": 0, "Premultiplied Color": 0, "Threshold": 1}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0005 | full-scale-mismatch | 65535 | 18485.6960 | 1.0000 | `[6971, 501, 932, 65535]` | `{"Color Keep": 1, "Color Space": 4, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 1, "Per Color": 1, "Premultiplied Color": 1, "Threshold": 1}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0008 | full-scale-mismatch | 65535 | 2443.2030 | 1.0000 | `[3781, 501, 932, 4555]` | `{"Color Keep": 0, "Color Space": 6, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 1, "Per Color": 0, "Premultiplied Color": 0, "Threshold": 0}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0009 | full-scale-mismatch | 65535 | 3653.6748 | 0.9899 | `[1198, 505, 606, 12312]` | `{"Color Keep": 0, "Color Space": 3, "Edge Blur": null, "Edge Thin": null, "Force Lower Precision": 3, "Per Color": 1, "Premultiplied Color": 0, "Threshold": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0015 | full-scale-mismatch | 65535 | 27689.3273 | 0.5206 | `[25946, 726, 26232, 31774]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 424, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0017 | full-scale-mismatch | 65535 | 30081.2208 | 0.5206 | `[27106, 817, 26116, 38913]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0018 | full-scale-mismatch | 65535 | 27311.1118 | 0.5206 | `[23417, 0, 23361, 37834]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0019 | full-scale-mismatch | 65535 | 31622.3150 | 0.5206 | `[38875, 0, 23361, 37834]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_blur_exact | olmdistancegradation_blur__case_0029 | full-scale-mismatch | 65535 | 32604.0018 | 0.5206 | `[30168, 0, 40375, 41251]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 158, "Interpolation Mode": 1, "Invert": 1, "Outside Threshold": 13, "Power": 0.00999999977648, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0010 | full-scale-mismatch | 65023 | 9878.8198 | 0.5206 | `[6874, 0, 26503, 6874]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 63, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 82, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0011 | full-scale-mismatch | 65023 | 24970.0999 | 0.5206 | `[28654, 0, 26503, 28654]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 348, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 0, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0012 | full-scale-mismatch | 65023 | 15805.4053 | 0.5206 | `[24241, 741, 25868, 5425]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 122, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0013 | full-scale-mismatch | 65023 | 23549.7955 | 0.5206 | `[25215, 712, 25989, 24033]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 53, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0014 | full-scale-mismatch | 65381 | 25654.6948 | 0.5206 | `[25623, 852, 26005, 29989]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 424, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0016 | full-scale-mismatch | 65535 | 29418.4528 | 0.5206 | `[26707, 1404, 26065, 37834]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 0, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0020 | full-scale-mismatch | 65535 | 32084.1215 | 0.5206 | `[40998, 0, 22083, 37834]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0021 | full-scale-mismatch | 65535 | 22540.5218 | 0.5206 | `[37820, 0, 21014, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 78, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 402, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0022 | full-scale-mismatch | 65535 | 23522.5731 | 0.5206 | `[38016, 0, 24241, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 36, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 11, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0023 | full-scale-mismatch | 65535 | 24216.8710 | 0.5206 | `[41286, 0, 23646, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 36, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 0, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0024 | full-scale-mismatch | 65535 | 20883.9628 | 0.5206 | `[34179, 0, 19120, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 3, "Invert": 0, "Outside Threshold": 17, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0025 | full-scale-mismatch | 65535 | 21611.6457 | 0.5206 | `[20747, 0, 34208, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 3, "Invert": 1, "Outside Threshold": 13, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0026 | full-scale-mismatch | 65535 | 22062.2820 | 0.5206 | `[20458, 0, 34171, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 2.59740734100342, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0027 | full-scale-mismatch | 65535 | 21517.6230 | 0.5206 | `[21464, 454, 26415, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 2.59740734100342, "Render Mode": 2, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0028 | full-scale-mismatch | 65535 | 23509.4951 | 0.5206 | `[22809, 860, 26057, 39032]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 0.40016460418701, "Render Mode": 2, "Use Background Color": 1}` |

Interpretation:
- `full-scale-mismatch` is too large to treat as rounding; inspect parameter replay/color management/effect path before tuning kernels.
- `candidate-close-to-input` suggests the effect path may not have applied or a controlling parameter was replayed incorrectly.
- `candidate-looks-8bit-quantized` suggests a bit-depth/writeback path issue.
