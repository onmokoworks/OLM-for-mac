# OLMToonDilate same-source public paired replay — 2026-08-13

Status: **PASS_EXACT12_PAIRED_PUBLIC_OWNER**.

The exact four fixture families at PF8/PF16/PF32 (12 cells) use identical active, padded payload, extent, origin, flags, rowbytes, and output hashes across the actual Windows AEX public Smart entry and the isolated Mac public `EffectMain`. Windows materializes Radius as f32 at its pinned internal seam; Mac receives the requested f64 value, and both produce the same effective radius and byte-exact output.

SmartPre requests preserve-RGB=false on both owners. Windows output flag `+0x22` and Mac `PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS` are both 1. The Mac replay also closes 12 WorldSuite error/NULL/exception paths with exact callback counts and complete input/output/header/padding/guard immutability.

This is not an AEXCompat, native-Windows, installed-binary, or real-After-Effects-host claim. The isolated Debug binary hash is intentionally observational and excluded because transient build paths change it.
