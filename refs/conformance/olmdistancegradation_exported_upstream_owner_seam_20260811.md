# OLMDistanceGradation exported upstream owner seam

Status: **BLOCKED_AFTER_SMART_PRE_RENDER_AT_LOAD_LIBRARY_W**.

The unchanged 2025 Windows AEX completes exported `SMART_PRE_RENDER` with error 0, enters `SMART_RENDER`, and now passes the previously missing `tolower`, `toupper`, `GetModuleHandleExA`, and `GetModuleFileNameW` host boundaries. It next stops explicitly at the generic `kernel32.dll!LoadLibraryW` import; cleanup completes and there are no unsupported Adobe suite calls.

The bounded numerical product is already exact for 24 cells: PF8/PF16/PF32 × Constant/Linear × Blur Mode 2/3 × Background off/on. That evidence covers the actual field-generation/blur/typed-compose or PF32 whole-owner numerical chains, but it does not yet promote them to an exported Smart owner claim. PF8/PF16 legacy `PF_Cmd_RENDER` remains compose-only over a preseeded green-lane field, and the actual AEX exposes no PF32 SmartRender branch.

The next host requirement is bounded, generic `LoadLibraryW` module/path resolution and lifetime/error semantics. No AEXCompat source was changed by this OLM evidence commit.
