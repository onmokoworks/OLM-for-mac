# OLMBlur UPDATE_PARAMS_UI actual-AEX contract — 2026-08-10

## Result

The public `PF_Cmd_UPDATE_PARAMS_UI` (`14`) path is now exact on its observed
success path. Both the pinned 2025 Windows AEX and the Mac production dispatcher
perform this sequence:

1. Convert `in_data->effect_ref` to an `AEGP_EffectRefH` with plug-in ID `0`.
2. Acquire effect parameter stream index `2` (`Blur Smoothness`).
3. Read its current dynamic-stream flags.
4. Set `AEGP_DynStreamFlag_HIDDEN` (`2`) with `undoable=false`, `set=true`.
5. Dispose the stream, then dispose the effect.

This explains the prior Mac UI discrepancy: `Blur Smoothness` was registered as
a normal parameter but the Mac dispatcher silently ignored the command that the
Windows implementation uses to hide it.

## Evidence

- AEX: `aex/OLMBlur/Plugins/64/2025/OLMBlur.aex`
- SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Exported entry: `0x18000a970`
- Machine-readable observation:
  `refs/conformance/olmblur_update_params_ui_actual_aex_20260810.json`
- Focused executable check:
  `python3 tools/emulation/test_olmblur_update_params_ui_actual_aex_20260810.py`
- Result:
  `PASS_OLMBLUR_UPDATE_PARAMS_UI_ACTUAL_AEX_20260810 calls=6 hidden_param=2`
- Universal-capable Xcode target build: `BUILD SUCCEEDED` for the Debug target
  after this change.

The focused check executes the actual AEX under Unicorn and separately compiles
the production `mac/OLMBlur/OLMBlur.cpp` dispatcher against SDK suite structs.
The production probe rejects any parameter index, flag, boolean, handle, plug-in
ID, ordering, or disposal mismatch.

## Evidence boundary

Proven here: the successful public-command AEGP call sequence and Mac dispatcher
equivalence. Not proven here: injected host-suite failure behavior, the native AE
visual layout itself, other commands, or render-pixel equivalence.
