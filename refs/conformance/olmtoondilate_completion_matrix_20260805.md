# OLMToonDilate completion matrix — 2026-08-05

The bounded SmartRender campaign covers sequence setup, SmartPreRender, and SmartRender entrypoints; PF8/PF16/PF32; integer radii 0–4; three independent fractional-radius cases; padded partial geometry; frontier/tie/corner behavior; and probe-local nonzero extents.

The empty-axis geometry now covers PF8 empty-width (`0x1`), PF16 empty-height (`1x0`), and PF32 both-axes-empty (`0x0`) worlds through actual command `0x18` and production `EffectMain`, including nonzero-origin zero-size extent headers, backing sentinels, and guards.

Largest remaining boundaries are legacy Render, the exact actual-AEX composition-width metadata field/layout, and execution under a real AE host. None are inferred from the current probe-local seams.

The legacy `PF_Cmd_RENDER` (`0x0b`) feasibility probe returned without acquiring PF World Suite or producing the expected output under the current probe ABI. It is recorded as unproved, not treated as parity or as evidence that the AEX lacks the command.

The AE-free installed completion route now links actual `0x17/0x18` entrypoint evidence, all typed workers/writers, the production adapter, current source identity, and the installed signed Universal binary identity. The installed arm64 slice is also dynamically loaded and its exported `EffectMain` independently executes SmartPreRender/SmartRender with exact PF8, PF16, and bitwise-exact PF32 visible words and padding. AE-host rendering remains outside the claim.
