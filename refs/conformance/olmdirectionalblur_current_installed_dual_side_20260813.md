# DirectionalBlur current installed dual-side replay (2026-08-13)

Status: `PASS_OLMDIRECTIONALBLUR_CURRENT_INSTALLED_DUAL_SIDE_TYPE2_ALL_DEPTHS_AE_FREE`

- Both Universal slices, fixed 32x18 dual-side Type2 at PF8/PF16/PF32: 3/3 exact per slice.
- Per-depth source-bit mutations: 3/3 fail-closed and output untouched per slice.
- SmartPre/Smart lifecycle, 21 params, padding and input immutability are exact.
- x86_64 executes under Rosetta; AE was not launched.

Boundary: Both current installed Universal slices of DirectionalBlur match their source-built real-SDK SmartPreRender to SmartRender route for the fixed 32x18 dual-side Type2 tuple at PF8, PF16 and PF32, including 21 parameter checkout/checkin operations, input/noise optional lifecycle, padding and input immutability. Per-depth source-bit mutations fail closed with untouched output on each slice. The x86_64 route is executed under Rosetta. This is AE-free dlopen evidence and does not generalize the fixed actual-AEX source/tuple contract or claim native After Effects.
