# OLMDistanceGradation PF32 Power Universal macOS 11 candidate

Status: **PASS_DISTANCE_PF32_POWER_FRESH_UNIVERSAL_MACOS11_CANDIDATE_SOURCE_RUNTIME_16_OF_16**.

A fresh isolated Debug build explicitly sets `MACOSX_DEPLOYMENT_TARGET=11.0`. The ad-hoc signed bundle is strict/deep-valid and contains x86_64 plus arm64 slices; Info.plist and both LC_BUILD_VERSION commands report 11.0. Within the two AE entrypoints checked, both slices expose `_EffectMain` and intentionally omit `_PluginDataEntryFunction2`, matching the Distance PiPL `CodeMac` contract; other global-defined implementation symbols are outside this claim. Separate per-architecture source-runtime harnesses retain the eight native-UCRT exact cells. The earlier 26.2-minimum candidate is superseded. No install, identity, MediaCore, AE, or numerical evidence change occurred.
