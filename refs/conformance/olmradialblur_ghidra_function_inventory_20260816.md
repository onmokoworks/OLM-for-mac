# OLMRadialBlur Ghidra function inventory (initial pass)

> **Superseded.** This document records the initial reachability pass only. The
> completed 362/362 semantic inventory, final live Ghidra names, callback
> appendix, and bounded confidence decisions are in
> `olmradialblur_ghidra_function_inventory_complete_20260816.md`. The counts
> below such as “98 unreached” and “243 automatic names” are historical and
> must not be treated as the current state.

Date: 2026-08-16

Target: `plugins_2025/OLMRadialBlur.aex`

Target SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`

This inventory was collected through the live Ghidra MCP bridge from the
`OLM2025` project. It is an analysis ledger, not a numerical-conformance claim.

## Inventory

- Ghidra functions in the program: 469
- Functions before the compiler/runtime boundary at `0x18001ce70`: 362
- Functions successfully decompiled through MCP: 362/362
- Discovered C++ vtables: 36
- Unique function targets referenced by scanned vtable slots: 87
- Functions reachable from `entry_point` plus all discovered vtable targets: 264
- Functions not yet reached by that static direct-call graph: 98
- Reachable functions still carrying automatic `FUN_...` names: 243

The 98 unreached functions are not automatically dead. They can include
callbacks referenced through non-vtable data, exception cleanup, template
helpers, or functions whose call was optimized into an indirect dispatch.

## High-confidence names applied in Ghidra

| Address | Name |
| --- | --- |
| `0x1800104a0` | `RadialBlur_PF_Cmd_ABOUT` |
| `0x18000b7c0` | `EffectBase_Construct` |
| `0x18000b8e0` | `RadialBlur_PF_Cmd_GLOBAL_SETUP` |
| `0x180017d60` | `RadialBlur_LockGlobalData` |
| `0x18000b9d0` | `RadialBlur_PF_Cmd_GLOBAL_SETDOWN` |
| `0x180006d10` | `RadialBlur_RenderPipeline_PF16` |
| `0x180007520` | `RadialBlur_RenderPipeline_PF8` |
| `0x180007d30` | `RadialBlur_RenderPipeline_PF32` |
| `0x180017260` | `RadialBlur_PixelAddress_PF8` |
| `0x180017290` | `RadialBlur_PixelAddress_PF16` |
| `0x1800172c0` | `RadialBlur_PixelAddress_PF32` |
| `0x1800172f0` | `RadialBlur_ReadPixel_PF8_to_F32` |
| `0x180017360` | `RadialBlur_ReadPixel_PF16_to_F32` |
| `0x1800173d0` | `RadialBlur_ReadPixel_PF32_to_F32` |
| `0x180017400` | `RadialBlur_WritePixel_F32_to_PF8` |
| `0x180017440` | `RadialBlur_WritePixel_F32_to_PF16` |
| `0x180017490` | `RadialBlur_WritePixel_F32_to_PF32` |

## Windows numerical leaves found

The plugin imports `log2f`, `sin`, `cos`, `expf`, and `atan2f`. Direct callers
identified by the first pass include:

- `atan2f`: `FUN_180001b10`, `FUN_18000a850`
- `sin`/`cos`: `RadialBlur_rotation_render`, `FUN_1800056f0`
- `log2f`: `FUN_180009a10`
- `expf`: `FUN_18000b680`

These functions are priority seams for Windows/Mac exactness because the CRT
leaf can differ even when surrounding control flow is identical.

## Finite completion rule

The Ghidra pass is complete when every one of the 362 plugin functions is in
exactly one class:

1. public-entry reachable and mapped to the Mac implementation;
2. public-entry reachable Windows-only runtime/SDK glue;
3. unreachable from exported commands, with the indirect-reference reason
   recorded; or
4. intentionally unsupported and fail-closed at the Mac public boundary.

Next, classify the 98 non-reached functions through non-vtable data references,
then name the remaining 243 reachable automatic functions from the leaves
upward. Geometry tests should be added only when needed to distinguish a branch
or validate a mapped function, rather than as an unbounded search.
