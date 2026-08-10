# OLMToonDilate completion matrix — 2026-08-05

The bounded campaign covers sequence setup, SmartPreRender, SmartRender, and the public legacy Render entrypoint; PF8/PF16/PF32; integer radii 0–4; three independent fractional-radius cases; padded partial geometry; frontier/tie/corner behavior; and probe-local nonzero extents.

The hostless public setup gate now captures the actual AEX `GLOBAL_SETUP` payload and complete one-row `PARAMS_SETUP` structure. Production and PiPL match the raw capability flags, parameter name/type, disk ID, flags/UI flags, ranges, default, precision, and curve tolerance. Native AE control layout remains a separate host boundary.

The empty-axis geometry now covers PF8 empty-width (`0x1`), PF16 empty-height (`1x0`), and PF32 both-axes-empty (`0x0`) worlds through actual command `0x18` and production `EffectMain`, including nonzero-origin zero-size extent headers, backing sentinels, and guards.

The downsample radius contract is now closed at the worker boundary. Actual PF8/PF16/PF32 workers read `PF_InData.downsample_x.num/den` at offsets `0x11c/0x120` and compute `ceil(radius * num / den)`. At radius 2.01, downsample ratios `1/1`, `1/2`, and `2/1` produce effective radii `3`, `2`, and `5`; actual AEX and production SmartPreRender/SmartRender are raw-exact for the corresponding composition-width/output-width ratios `1`, `2`, and `0.5`.

The legacy `PF_Cmd_RENDER` (`0x0b`) dispatches to `FUN_1801a7840`, a constant-zero no-op. Owner recovery uses only PF Handle Suite; no render suite, parameter interpretation, world read, or pixel callback occurs. Radius 0 and 2.01 at PF8/PF16/PF32 leave input, output, parameter headers, padding, and guards untouched. Production now matches this public-entry contract and keeps rendering exclusively on the advertised Smart Render route.

The remaining boundary in this area is execution under a real AE host; the hostless evidence does not claim which fallback commands a future AE version may choose.

The AE-free installed completion route now links actual `0x17/0x18` entrypoint evidence, all typed workers/writers, the production adapter, current source identity, and the installed signed Universal binary identity. The installed arm64 slice is also dynamically loaded and its exported `EffectMain` independently executes SmartPreRender/SmartRender with exact PF8, PF16, and bitwise-exact PF32 visible words and padding. AE-host rendering remains outside the claim.
