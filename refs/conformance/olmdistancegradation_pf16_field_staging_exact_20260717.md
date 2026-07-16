# OLMDistanceGradation PF16 field/staging exact differential

Date: 2026-07-17

## Result

The hash-pinned Windows AEX and current Mac production source were run on the
same non-degenerate 8x5 PF16 source, padded rowbytes, and 1/1 downsample ratios.

- Actual AEX field generator entries: 2
- Actual AEX compose entries: 40
- Field words: 40/40 exact, word_diff_count=0
- Final PF16 output: 40/40 exact, byte_diff_count=0
- Source and destination padding canaries were preserved.

The previous comparison was invalid for localization because it wrote
WIDTH/HEIGHT into the PF_InData downsample numerators. That staged the AEX
fixture as 64x25 while the source oracle rendered 8x5. It also used an
all-opaque input and manually disabled the AEX degenerate flag.

## Production correction

FUN_181170480 stores PF16 channels as float * 32768 followed by truncating
float-to-int conversion. The Mac clamp16 helper used +0.5 rounding. Before the
correction, the aligned fixture had four red words with AEX = Mac - 1;
removing +0.5 makes the complete bounded output byte-exact.

## Verification

The following commands all passed:

- python3 tools/emulation/test_dg_pf16_field_staging_differential_20260717.py
- python3 tools/emulation/test_dg_pf16_source_oracle_20260717.py
- bash tools/emulation/dg_renderbits_real_harness_20260716.sh
- python3 tools/emulation/test_olmdistancegradation_renderbits_host_resize_staging_20260717.py
- xcodebuild -project mac/OLMDistanceGradation/Mac/OLMDistanceGradation.xcodeproj -configuration Debug build CODE_SIGNING_ALLOWED=NO

This is bounded Mac-local AEX/source equivalence and a successful universal
Debug build. It is not Windows AE or Mac AE exactness.
