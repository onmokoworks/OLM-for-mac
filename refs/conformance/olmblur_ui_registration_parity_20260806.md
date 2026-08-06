# OLMBlur UI registration parity — 2026-08-06

The hash-pinned 2025 Windows AEX public export was executed directly for both
`PF_Cmd_GLOBAL_SETUP` and `PF_Cmd_PARAMS_SETUP`. The Mac `EffectMain` was then
compiled from current source and invoked through equivalent bounded callbacks.

## Exact public payloads

- `GLOBAL_SETUP`: `my_version=0x00090800`, `out_flags=0x06000040`, and
  `out_flags2=0x08001400` are byte-exact. See
  `olmblur_global_setup_actual_aex_20260806.json`.
- `PARAMS_SETUP`: all five `add_param` rows are exact after excluding pointer
  addresses and inactive union residue. Disk ID, type, active value/default and
  range fields, `flags`, `ui_flags`, precision, display flags, and float-slider
  flags are compared. See `olmblur_params_setup_actual_aex_20260806.json`.

The direct run identified four production differences, now corrected:

1. Blur Amount registers raw precision `2`.
2. Blur Smoothness registers percent display flag `1`.
3. Legacy registers current value `true` with new-effect default `false`.
4. Legacy includes `PF_ParamFlag_USE_VALUE_FOR_OLD_PROJECTS` (`0x80`).

`xcodebuild` completed a Debug Universal build with `arm64` and `x86_64` slices.
The installed bundle was not replaced because After Effects was running; this
record therefore makes no current-installed-bundle or native AE UI claim.

## Evidence boundary

This proves the raw registration contract at the public entrypoint for the
five parameter rows and the three global setup words. It does not prove how a
specific AE version localizes or visually lays out the controls, and it does
not extend any render-exact claim.
