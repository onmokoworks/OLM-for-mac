# DistanceGradation current installed Mode5 boundary (2026-08-13)

Status: `PASS_OLMDISTANCEGRADATION_CURRENT_INSTALLED_MODE5_6_POWER_FAILCLOSED_8_AE_FREE`

- Both Universal slices, fixed17x11 PF32 Mode5 Constant/Linear/Sphere × background off/on: 6/6 installed/source exact per slice.
- Both slices, PF32 Power blur modes 2/3/4/5 × background off/on: 8/8 fail-closed per slice, output untouched.
- x86_64 executes under Rosetta; AE was not launched.

Boundary: Both current installed Universal slices of DistanceGradation match their source-built real-SDK Smart path for six fixed17x11 PF32 Mode5 Constant/Linear/Sphere cells per slice, including padding and callback lifecycle. All eight PF32 Power cells per slice remain fail-closed with untouched output because native Windows UCRT powf has not been captured. The x86_64 route is executed under Rosetta. This AE-free dlopen replay does not generalize beyond the fixed contract or claim native After Effects.
