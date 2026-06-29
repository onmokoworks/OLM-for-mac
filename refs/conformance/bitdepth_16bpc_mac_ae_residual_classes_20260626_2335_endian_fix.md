# 16bpc Mac AE Residual Classes - 2026-06-26 Endian-Fix Reverify

Status: classified, not AE exact.

This classification uses the Mac AE batch reverified after fixing 16-bit PNG ImageMagick endian decoding in `refs/scripts/verify_manifest.py`.

| Label | Count |
| --- | ---: |
| candidate-looks-8bit-quantized | 1 |
| full-scale-mismatch | 3 |
| large-structured-mismatch | 17 |
| olmblur-16bpc-legacy-border-plus-near-1lsb | 1 |
| olmblur-16bpc-near-1lsb | 6 |

| Plugin slice | Residual labels |
| --- | --- |
| olmblur | olmblur-16bpc-legacy-border-plus-near-1lsb=1, olmblur-16bpc-near-1lsb=6 |
| olmcolorkey | full-scale-mismatch=1 |
| olmdistancegradation_basic | large-structured-mismatch=4 |
| olmdistancegradation_blur | large-structured-mismatch=1 |
| olmdistancegradation_extended | candidate-looks-8bit-quantized=1, full-scale-mismatch=2, large-structured-mismatch=12 |

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
| `Blur Smoothness=100` | 7 |
| `olmblur` | 7 |
| `Bias Direction=1` | 6 |
| `Interpolation Mode=1` | 5 |
| `Legacy=0` | 5 |
| `olmdistancegradation_basic` | 4 |
| `Blur Amount=5` | 3 |
| `Interpolation Mode=4` | 3 |
| `Number of Repeat=10` | 3 |
| `Number of Repeat=2` | 3 |
| `Blur Amount=129.399993896484` | 2 |
| `Interpolation Mode=3` | 2 |
| `Legacy=1` | 2 |
| `Power=2.59740734100342` | 2 |

| Request | Case | Label | Max | Mean | Candidate 8bit score | Channel mean delta RGBA | Key params |
| --- | --- | --- | ---: | ---: | ---: | --- | --- |
| bitdepth16_olmblur_exact | olmblur__case_0001 | olmblur-16bpc-near-1lsb | 2 | 0.0000 | 0.8825 | `[0, 0, 0, 0]` | `{"Bias Direction": 1, "Blur Amount": 129.399993896484, "Blur Smoothness": 100, "Legacy": 0, "Number of Repeat": 2}` |
| bitdepth16_olmblur_exact | olmblur__case_0002 | olmblur-16bpc-near-1lsb | 2 | 0.0000 | 0.8825 | `[0, 0, 0, 0]` | `{"Bias Direction": 2, "Blur Amount": 129.399993896484, "Blur Smoothness": 100, "Legacy": 0, "Number of Repeat": 2}` |
| bitdepth16_olmblur_exact | olmblur__case_0003 | olmblur-16bpc-near-1lsb | 2 | 0.0004 | 0.6667 | `[0, 0, 0, 0]` | `{"Bias Direction": 1, "Blur Amount": 248.600006103516, "Blur Smoothness": 100, "Legacy": 1, "Number of Repeat": 10}` |
| bitdepth16_olmblur_exact | olmblur__case_0004 | olmblur-16bpc-near-1lsb | 2 | 0.0000 | 0.8747 | `[0, 0, 0, 0]` | `{"Bias Direction": 1, "Blur Amount": 125.599998474121, "Blur Smoothness": 100, "Legacy": 0, "Number of Repeat": 4}` |
| bitdepth16_olmblur_exact | olmblur__case_0005 | olmblur-16bpc-near-1lsb | 2 | 0.0000 | 0.7816 | `[0, 0, 0, 0]` | `{"Bias Direction": 1, "Blur Amount": 5, "Blur Smoothness": 100, "Legacy": 0, "Number of Repeat": 2}` |
| bitdepth16_olmblur_exact | olmblur__case_0006 | olmblur-16bpc-near-1lsb | 2 | 0.0002 | 0.4385 | `[0, 0, 0, 0]` | `{"Bias Direction": 1, "Blur Amount": 5, "Blur Smoothness": 100, "Legacy": 0, "Number of Repeat": 10}` |
| bitdepth16_olmblur_exact | olmblur__case_0007 | olmblur-16bpc-legacy-border-plus-near-1lsb | 383 | 0.0002 | 0.2569 | `[0, 0, 0, 0]` | `{"Bias Direction": 1, "Blur Amount": 5, "Blur Smoothness": 100, "Legacy": 1, "Number of Repeat": 10}` |
| bitdepth16_olmcolorkey_exact | olmcolorkey__case_0009 | full-scale-mismatch | 65535 | 100.9505 | 1.0000 | `[2, 0, 3, 398]` | `{"Color Keep": 0, "Color Space": 3, "Edge Blur": null, "Edge Blur Amount": 0, "Edge Blur Direction": 3, "Edge Blur Distance Type": 1, "Edge Thin": null, "Edge Thin Amount": 25, "Edge Thin Distance Type": 2, "Force Lower Precision": 3, "Per Color": 1, "Per Component": 1, "Premultiplied Color": 0, "Threshold": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0015 | large-structured-mismatch | 423 | 13.7867 | 0.9342 | `[12, 1, 1, 41]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 424, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0017 | large-structured-mismatch | 2311 | 23.6026 | 0.9624 | `[34, 4, 6, 51]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0018 | large-structured-mismatch | 2156 | 13.4018 | 0.9035 | `[6, 0, 48, 0]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_basic_exact | olmdistancegradation_basic__case_0019 | large-structured-mismatch | 2156 | 23.3395 | 0.9037 | `[46, 0, 48, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_blur_exact | olmdistancegradation_blur__case_0029 | large-structured-mismatch | 5892 | 74.6745 | 0.9115 | `[16, 0, 136, 146]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 158, "Interpolation Mode": 1, "Invert": 1, "Outside Threshold": 13, "Power": 0.00999999977648, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0010 | large-structured-mismatch | 55536 | 2193.7995 | 0.7834 | `[4388, 0, 0, 4388]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 63, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 82, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0011 | full-scale-mismatch | 65347 | 248.6360 | 0.8704 | `[497, 0, 0, 497]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 348, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 0, "Power": 1, "Render Mode": 1, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0012 | large-structured-mismatch | 55896 | 1167.9616 | 0.9451 | `[117, 85, 86, 4383]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 3, "Inside Threshold": 122, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0013 | large-structured-mismatch | 9170 | 49.6547 | 0.9632 | `[71, 34, 36, 57]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 53, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0014 | large-structured-mismatch | 9640 | 39.8509 | 0.9282 | `[48, 35, 35, 41]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 424, "Interpolation Mode": 2, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0016 | candidate-looks-8bit-quantized | 65021 | 160.3788 | 1.0000 | `[146, 134, 134, 229]` | `{"BG Color": [0, 0, 0, 1], "Gradation Color": [1, 0, 0, 1], "In/Out": 1, "Inside Threshold": 0, "Interpolation Mode": 2, "Invert": 1, "Outside Threshold": 204, "Power": 1, "Render Mode": 2, "Use Background Color": 0}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0020 | large-structured-mismatch | 61165 | 10.6907 | 0.9954 | `[21, 0, 22, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 1, "Inside Threshold": 78, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 204, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0021 | large-structured-mismatch | 61165 | 10.7051 | 1.0000 | `[21, 0, 22, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 78, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 402, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0022 | large-structured-mismatch | 61165 | 4575.0025 | 1.0000 | `[8934, 0, 9366, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 36, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 11, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0023 | large-structured-mismatch | 61165 | 225.9017 | 1.0000 | `[441, 0, 462, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 36, "Interpolation Mode": 1, "Invert": 0, "Outside Threshold": 0, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0024 | large-structured-mismatch | 61163 | 5054.0634 | 0.7184 | `[9869, 0, 10347, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 3, "Invert": 0, "Outside Threshold": 17, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0025 | large-structured-mismatch | 54302 | 1018.0898 | 0.7572 | `[1988, 0, 2084, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 3, "Invert": 1, "Outside Threshold": 13, "Power": 1, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0026 | large-structured-mismatch | 61165 | 11754.5770 | 0.9037 | `[22953, 0, 24066, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 2.59740734100342, "Render Mode": 1, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0027 | full-scale-mismatch | 65530 | 5299.6384 | 0.9596 | `[19152, 1212, 835, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 2.59740734100342, "Render Mode": 2, "Use Background Color": 1}` |
| bitdepth16_olmdistancegradation_extended_exact | olmdistancegradation_extended__case_0028 | large-structured-mismatch | 57184 | 2154.4740 | 0.9896 | `[7282, 800, 536, 0]` | `{"BG Color": [1, 0, 0, 1], "Gradation Color": [0.1098041459918, 0, 0.93333333730698, 1], "In/Out": 3, "Inside Threshold": 158, "Interpolation Mode": 4, "Invert": 1, "Outside Threshold": 13, "Power": 0.40016460418701, "Render Mode": 2, "Use Background Color": 1}` |

Interpretation:
- `olmblur-16bpc-near-1lsb` means every nonzero OLMBlur delta is within about one AE 16bpc output unit, which appears as `max_diff=2` in exported PNG space; investigate final rounding/writeback before kernel tuning.
- `olmblur-16bpc-legacy-border-plus-near-1lsb` means the same near-1LSB family is present, plus a small Legacy-only border/seed anomaly.
- `full-scale-mismatch` is too large to treat as rounding; inspect parameter replay/color management/effect path before tuning kernels.
- `candidate-close-to-input` suggests the effect path may not have applied or a controlling parameter was replayed incorrectly.
- `candidate-looks-8bit-quantized` suggests a bit-depth/writeback path issue.
