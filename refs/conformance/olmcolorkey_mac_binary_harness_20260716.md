# OLMColorKey Mac Binary Harness

Status: `pass_mac_binary_fixture`.

This is bounded Mac executable evidence, not AE host execution and not an `AE exact` claim. The harness invokes the checked-in arm64 Mach-O `cli/OLMColorKey/olmcolorkey_cli` with a generated 2x2 RGBA8 fixture and JSON parameters. The two exact red pixels are kept and replaced with green; the non-matching green and blue pixels are cleared. The output is decoded and compared as raw RGBA bytes.

The checked-in plug-in bundle remains host-bound. `nm -gU` reports `_EffectMain` at `0x75c` and `_PluginDataEntryFunction2` at `0x6b4` in the archived arm64/x86_64 universal binary. No standalone worker export exists. Calling `EffectMain` requires AE-owned `PF_InData`, `PF_OutData`, `PF_ParamDef`, `PF_EffectWorld`, and suite pointers, so this lane does not claim plug-in host execution. The minimal next harness is an AE host run or a host-owned PF world/suite shim calling `EffectMain(PF_Cmd_SMART_RENDER)` with captured typed worlds.

## Exact commands

```text
python3 scripts/exercise_olmcolorkey_mac_binary_harness_20260716.py
python3 tests/test_olmcolorkey_mac_binary_harness_20260716.py
```

The script writes the machine-readable result to `refs/conformance/olmcolorkey_mac_binary_harness_20260716.json`, including the executable SHA-256, `file` identity, command, fixture dimensions, raw output SHA-256, and plug-in export boundary.

The Mac plug-in target also compiled successfully into a temporary arm64 `.plugin` product. This confirms the source/build path is locally available; it does not execute the effect without AE.

```text
xcodebuild -project mac/OLMColorKey/Mac/OLMColorKey.xcodeproj -scheme OLMColorKey -configuration Debug -derivedDataPath /tmp/olmcolorkey_mac_harness_build_20260716 build CODE_SIGNING_ALLOWED=NO
result: ** BUILD SUCCEEDED **
```
