# OLMKiraKira Channel 2 BT.709 C++ correction (2026-07-12)

## FACT

- Windows runtime captured `0.79773343` for RGB `[230, 210, 60]` at the
  Channel 2 seed stage.
- Normalized BT.709 (`0.2126, 0.7152, 0.0722`) reproduces that value within
  `1e-7`; BT.601 does not.
- `refs/scripts/olmkirakira_cli.py` and `notes/IR_OLMKiraKira.md` already used
  BT.709, while both C++ implementations still used BT.601.

## Change

- `cli/OLMKiraKira/main.cpp`: Channel 2 seed luma now uses BT.709.
- `mac/OLMKiraKira/OLMKiraKira.cpp`: same correction in the AE host path.

## Verification

- `python3 refs/scripts/smoke_olmkirakira_channel2_bt709.py`: PASS.
- `refs/scripts/build_olmkirakira_cli.sh /tmp/olmkirakira_cli_bt709`: PASS.
- `xcodebuild -project mac/OLMKiraKira/Mac/OLMKiraKira.xcodeproj
  -configuration Debug build CODE_SIGNING_ALLOWED=NO`: `BUILD SUCCEEDED` for
  the universal arm64/x86_64 plug-in.
- `python3 refs/scripts/smoke_olmkirakira_cpp_cli.py --binary /tmp/olmkirakira_cli_bt709`:
  runner completed; its three broad experimental cases remain known-red
  (`max=29`, `31`, `233`). They do not prove AE exact and are not promoted.

This correction is binary/runtime-grounded but does not close KiraKira as a
whole. Merge compose, final quantization, and other modes remain separate.
