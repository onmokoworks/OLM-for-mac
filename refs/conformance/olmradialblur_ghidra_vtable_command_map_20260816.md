# OLMRadialBlur MyEffect / EffectBase vtable and PF_Cmd map

Target: Ghidra MCP default target, `OLMRadialBlur.aex`. No target switch.  
Authorities: Ghidra decompile/disassembly, `Headers/AE_Effect.h:1148-1193`, and retained actual-AEX/public-edge evidence under `refs/conformance/olmradialblur_*`.

## Object and vtable identity

- `EffectBase_Construct @ 0x18000b7c0` installs `EffectBase::vftable @ 0x180021b00`.
- Exported `entry_point @ 0x180010540`, command 1, allocates and zeroes a 0x1f8-byte object, calls `EffectBase_Construct`, then overwrites the vptr with `MyEffect::vftable @ 0x180021e98`.
- The object is stored in `out_data->global_data` as a PF handle. Every later handled command calls `RadialBlur_LockGlobalData @ 0x180017d60`, dispatches, then `RadialBlur_UnlockGlobalData @ 0x180017e10`.
- Slot addresses below are absolute data addresses; slot offsets are from the vptr.

## Complete vtable slot map

| Slot | EffectBase entry / target | MyEffect entry / target | Semantics in exported PF_Cmd path | Confidence |
|---|---|---|---|---|
| `+0x00` | `0x180021b00 → 0x180010470` | `0x180021e98 → 0x180010470` | Post-registration/global-setup hook. Called by `RadialBlur_PF_Cmd_GLOBAL_SETUP` after AEGP plugin registration. Target is a shared one-instruction `RET`; Ghidra's name `_guard_check_icall` is misleading here. Recommended semantic name: `EffectBase_OnGlobalSetupComplete_NoOp`. | High for call role and no-op; medium for original C++ method name |
| `+0x08` | `0x180021b08 → 0x180010470` | `0x180021ea0 → 0x180010470` | Pre-destruction/global-setdown hook. Called before parameter-handler cleanup and object destruction. Same shared `RET`. Recommended name: `EffectBase_OnGlobalSetdownBegin_NoOp`. | High for call role and no-op; medium for original name |
| `+0x10` | `0x180021b10 → EffectBase_SmartPreRender @ 0x18000bb30` | `0x180021ea8 → RadialBlur_SmartPreRender @ 0x180004010` | `PF_Cmd_SMART_PRE_RENDER`. Both checkout input request 0 and union its result/max rectangles into pre-render output. MyEffect additionally writes `PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS (1)` at output offset `+0x22`; the base implementation does not. | High |
| `+0x18` | `0x180021b18 → _purecall @ 0x18001f52c` | `0x180021eb0 → RadialBlur_ParamsSetup @ 0x1800034c0` | `PF_Cmd_PARAMS_SETUP`; registers the 31-entry parameter schema and writes `out_data->num_params = 0x1f`. Abstract/pure in EffectBase. | High |
| `+0x20` | `0x180021b20 → _purecall @ 0x18001f52c` | `0x180021eb8 → RadialBlur_RenderDispatcher @ 0x1800040f0` | Smart render owner used by both `PF_Cmd_SMART_RENDER` and `PF_Cmd_SMART_RENDER_GPU`. It checks out input/output through SmartRender callbacks, materializes parameters, branches on bitdepth 8/16/32, and calls the typed render pipeline. The GPU command passes an extra boolean 1, but this decompile does not establish a distinct GPU kernel. Recommended narrower name: `RadialBlur_SmartRenderDispatcher`. | High for SmartRender; medium for GPU/cached behavior |
| `+0x28` | `0x180021b28 → FUN_18000bc00 @ 0x18000bc00` | `0x180021ec0 → FUN_18000bc00 @ 0x18000bc00` | `PF_Cmd_USER_CHANGED_PARAM`; empty `RET`. Recommended name: `EffectBase_UserChangedParam_NoOp`. | High |
| `+0x30` | `0x180021b30 → FUN_18000bc10 @ 0x18000bc10` | `0x180021ec8 → RadialBlur_UpdateParamsUI @ 0x180003ca0` | `PF_Cmd_UPDATE_PARAMS_UI`. Base is empty. MyEffect enables/disables Noise Layer versus procedural noise controls and Zoom/Rotation offset controls, then invalidates/updates the effect UI through AEGP suites. | High |
| `+0x38` | `0x180021b38 → EffectBase_HandleCustomParamEvent @ 0x18000bc20` | `0x180021ed0 → EffectBase_HandleCustomParamEvent @ 0x18000bc20` | `PF_Cmd_EVENT`; generic custom parameter UI event routing (click/drag/draw/cursor-style event subtypes), using PF Handle, DRAWBOT, PF AE App and parameter-handler virtual callbacks. | High |
| `+0x40` | `0x180021b40 → EffectBase_CommandDispatcher @ 0x18000bf00` | `0x180021ed8 → EffectBase_CommandDispatcher @ 0x18000bf00` | `PF_Cmd_ARBITRARY_CALLBACK`; dispatches the arbitrary-data subcommand in `PF_ArbParamsExtra` (0..10) to virtual handler operations. It is not the exported PF_Cmd switch. Recommended name: `EffectBase_ArbitraryCallbackDispatcher`. | High |
| `+0x48` | `0x180021b48 → FUN_18000c0a0 @ 0x18000c0a0` | `0x180021ee0 → FUN_18000c0a0 @ 0x18000c0a0` | `PF_Cmd_SEQUENCE_SETUP`; returns 0 without allocating sequence state. | High |
| `+0x50` | `0x180021b50 → FUN_18000c0b0 @ 0x18000c0b0` | `0x180021ee8 → FUN_18000c0b0 @ 0x18000c0b0` | `PF_Cmd_SEQUENCE_SETDOWN`; returns 0. | High |
| `+0x58` | `0x180021b58 → FUN_18000c0c0 @ 0x18000c0c0` | `0x180021ef0 → FUN_18000c0c0 @ 0x18000c0c0` | `PF_Cmd_SEQUENCE_RESETUP`; returns 0. | High |
| `+0x60` | `0x180021b60 → FUN_18000c0e0 @ 0x18000c0e0` | `0x180021ef8 → FUN_18000c0e0 @ 0x18000c0e0` | `PF_Cmd_SEQUENCE_FLATTEN`; returns 0. | High |

The MyEffect table ends at `0x180021ef8`; `0x180021f00` begins unrelated RTTI data.

## Exported PF_Cmd switch

The authoritative public dispatcher is exported `entry_point / Ordinal_1 @ 0x180010540`. Command numbers below follow the immutable enumeration in `Headers/AE_Effect.h`.

| PF_Cmd value | Command | Slot address or direct target | Observed Windows AEX semantics | Confidence |
|---|---|---|---|---|
| 0 | `ABOUT` | direct `RadialBlur_PF_Cmd_ABOUT @ 0x1800104a0` | Writes “OLM RadialBlur 1.3” and description through PF ANSI Suite. | High |
| 1 | `GLOBAL_SETUP` | direct construction + `RadialBlur_PF_Cmd_GLOBAL_SETUP @ 0x18000b8e0`, then vslot `0x180021e98` | Allocates 0x1f8-byte persistent global object, installs MyEffect vtable, sets version/flags, registers “OLM RadialBlur”, calls no-op post-setup hook, stores global-data handle. | High |
| 2 | `UNUSED_0` | none | Falls through to return 0. | High |
| 3 | `GLOBAL_SETDOWN` | direct `RadialBlur_PF_Cmd_GLOBAL_SETDOWN @ 0x18000b9d0`, plus vslot `0x180021ea0` | Locks global object, calls no-op pre-setdown hook, destroys registered parameter handlers/string state, disposes global handle. Acquires/releases AEGP Compute Cache suite but no render-cache operation is visible. | High |
| 4 | `PARAMS_SETUP` | `0x180021eb0 (+0x18)` → `RadialBlur_ParamsSetup` | Registers parameter schema. | High |
| 5 | `SEQUENCE_SETUP` | `0x180021ee0 (+0x48)` → `FUN_18000c0a0` | Return 0; no sequence allocation. | High |
| 6 | `SEQUENCE_RESETUP` | `0x180021ef0 (+0x58)` → `FUN_18000c0c0` | Return 0. | High |
| 7 | `SEQUENCE_FLATTEN` | `0x180021ef8 (+0x60)` → `FUN_18000c0e0` | Return 0. | High |
| 8 | `SEQUENCE_SETDOWN` | `0x180021ee8 (+0x50)` → `FUN_18000c0b0` | Return 0. | High |
| 9 | `DO_DIALOG` | direct `FUN_18000c150 @ 0x18000c150` | Return 0; no dialog work. | High |
| 10 | `FRAME_SETUP` | direct `FUN_18000c100 @ 0x18000c100` | Return 0. | High |
| 11 | `RENDER` | direct `FUN_18000c140 @ 0x18000c140` | Return 0. The Windows AEX's classic render command does **not** call a typed render pipeline. | High |
| 12 | `FRAME_SETDOWN` | direct `FUN_18000c110 @ 0x18000c110` | Return 0. | High |
| 13 | `USER_CHANGED_PARAM` | `0x180021ec0 (+0x28)` → `FUN_18000bc00` | Empty return. | High |
| 14 | `UPDATE_PARAMS_UI` | `0x180021ec8 (+0x30)` → `RadialBlur_UpdateParamsUI` | Dynamic parameter enable/disable and effect UI invalidation. | High |
| 15 | `EVENT` | `0x180021ed0 (+0x38)` → `EffectBase_HandleCustomParamEvent` | Routes supported custom-parameter UI events. | High |
| 16 | `GET_EXTERNAL_DEPENDENCIES` | direct `FUN_18000c160 @ 0x18000c160` | Return 0; does not describe dependencies. | High |
| 17 | `COMPLETELY_GENERAL` | direct `FUN_18000c170 @ 0x18000c170` | Return 0. | High |
| 18 | `QUERY_DYNAMIC_FLAGS` | direct `FUN_18000c0d0 @ 0x18000c0d0` | Return 0; no dynamic flag adjustment. | High |
| 19 | `AUDIO_RENDER` | direct `FUN_18000c180 @ 0x18000c180` | Return 0. | High |
| 20 | `AUDIO_SETUP` | direct `FUN_18000c190 @ 0x18000c190` | Return 0. | High |
| 21 | `AUDIO_SETDOWN` | direct `FUN_18000c1a0 @ 0x18000c1a0` | Return 0. | High |
| 22 | `ARBITRARY_CALLBACK` | `0x180021ed8 (+0x40)` → `EffectBase_CommandDispatcher` | Generic arbitrary-param subcommand dispatcher. | High |
| 23 | `SMART_PRE_RENDER` | `0x180021ea8 (+0x10)` → `RadialBlur_SmartPreRender` | Checks out input request, unions result/max rectangles, advertises `RETURNS_EXTRA_PIXELS`. No pre-render payload/delete function is installed. | High |
| 24 | `SMART_RENDER` | `0x180021eb8 (+0x20)` → `RadialBlur_RenderDispatcher` | Actual CPU render owner; parameter checkout, 8/16/32 dispatch, typed pipeline. | High |
| 25–27 | `RESERVED1..3` | none | Fall through to return 0. | High |
| 28 | `GET_FLATTENED_SEQUENCE_DATA` | direct `FUN_18000c0f0 @ 0x18000c0f0` | Return 0; no flattened sequence data. | High |
| 29 | `TRANSLATE_PARAMS_TO_PREFS` | none | Falls through to return 0. | High |
| 30 | `RESERVED4` | none | Falls through to return 0. | High |
| 31 | `SMART_RENDER_GPU` | `0x180021eb8 (+0x20)` → `RadialBlur_RenderDispatcher`, extra flag 1 | Reuses CPU SmartRender dispatcher entry. The extra flag is not represented in Ghidra's recovered prototype and a distinct GPU computation is not established. | Medium |
| 32 | `GPU_DEVICE_SETUP` | direct `FUN_18000c120 @ 0x18000c120` | Return 0. | High |
| 33 | `GPU_DEVICE_SETDOWN` | direct `FUN_18000c130 @ 0x18000c130` | Return 0. | High |

## Cached and pre-render ambiguity flags

1. **Persistent global object is not pre-render cache.** The MyEffect instance is cached only as `PF_OutData::global_data` and locked for each command. No per-frame render result is proven cached there.
2. **Compute Cache usage is not established.** `GLOBAL_SETDOWN` acquires/releases `AEGP Compute Cache` v1, but the recovered body performs no identifiable cache lookup/store/eviction. Do not infer cached render reuse from the suite string alone.
3. **No `pre_render_data` handoff.** `RadialBlur_SmartPreRender` fills rectangles and flags, but does not set `PF_PreRenderOutput::pre_render_data` or `delete_pre_render_data_func`. SmartRender re-checks parameters through its own path.
4. **Base and derived pre-render differ.** `EffectBase_SmartPreRender` and `RadialBlur_SmartPreRender` are almost identical, but only MyEffect sets `PF_RenderOutputFlag_RETURNS_EXTRA_PIXELS`. Treating the base slot as the RadialBlur command target loses this behavior.
5. **Classic versus Smart render must not be conflated.** Windows `PF_Cmd_RENDER (11)` is a zero-return stub; the typed owner is `PF_Cmd_SMART_RENDER (24)`. The Mac source implements a classic `Render` public path too, so source-level command-surface parity does not prove that the Windows classic command renders.
6. **GPU reuse is ambiguous.** Command 31 reaches the same vslot as command 24 with an added flag, while GPU setup/setdown are stubs. This proves dispatch reuse, not GPU acceleration or cache identity.

## Existing evidence connection

- `refs/conformance/olmradialblur_smartrender_fullpath_connection_20260805.json` records the public chain `EffectMain(PF_Cmd_SMART_RENDER) → callbacks/param checkout → typed RenderWorld → cleanup → commit`, while explicitly excluding native AE callback-ABI proof.
- `refs/conformance/olmradialblur_public_completion_matrix_20260805.md` describes the production public command surface, but its classic `RENDER` implementation is a Mac-side surface fact; the Ghidra switch above shows the retained Windows AEX classic command is a stub.
- Actual-AEX typed render reports that hook owners `0x180007520`, `0x180006d10`, and `0x180007d30` connect downstream of `RadialBlur_RenderDispatcher`; they do not change the exported command-number mapping.

## Rename policy

No functions were renamed in this follow-up. The relevant implementation ranges are shared with other range agents and several functions already acquired names during their work. Recommended names only:

- `RadialBlur_RenderDispatcher` → `RadialBlur_SmartRenderDispatcher`
- `EffectBase_CommandDispatcher` → `EffectBase_ArbitraryCallbackDispatcher`
- `FUN_18000bc00` → `EffectBase_UserChangedParam_NoOp`
- `FUN_18000bc10` → `EffectBase_UpdateParamsUI_NoOp`
- `FUN_18000c0a0/c0b0/c0c0/c0e0` → sequence setup/setdown/resetup/flatten no-op names

No production source was edited.
