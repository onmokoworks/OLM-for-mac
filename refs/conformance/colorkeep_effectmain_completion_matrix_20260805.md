# ColorKeep public EffectMain completion matrix

| Public command | Actual 2025 AEX boundary | Mac production boundary | Status / strongest evidence |
|---|---|---|---|
| `ABOUT` | Not executed through public export | Production branch present | Partial; exact message and ANSI suite interaction remain open |
| `GLOBAL_SETUP` | Public export command 1 | Public production EffectMain | Exact 12-byte version/flags payload; `colorkeep_global_setup_actual_aex_20260805.json` |
| `GLOBAL_SETDOWN` | Public export command 3; all argument regions traced | Public production EffectMain with invalid sentinel pointers | Exact argument-independent no-op returning `PF_Err_NONE`; no argument reads/writes |
| `PARAMS_SETUP` | Public export command 4; 101 add-param callbacks normalized | Public production EffectMain with real SDK callback | Exact disk IDs, types, flags, ui_flags, slider ranges/default and color defaults. Both binaries contain the same two display-name literals, but per-row binding/localization remains host-initializer-bound; `colorkeep_parameter_ui_closure_20260806.md` |
| `RENDER` PF8 | Actual typed worker oracle | Public production legacy EffectMain | Exact padded-frame and multicolor fixtures |
| `RENDER` PF16 | Actual typed worker oracle | Public production legacy EffectMain | Exact padded-frame, quantization, and extended-range fixtures |
| `RENDER` PF32 | Actual typed worker oracle | Legacy command has no PF32 dispatch | Not applicable to legacy path; PF32 is Smart Render only |
| `USER_CHANGED_PARAM` | Public export command 13; changed-index extra traced | Public production EffectMain | Exact 100-control enable surface; actual ignores changed-index extra |
| `UPDATE_PARAMS_UI` | Public export command 14 | Public production EffectMain | Exact 100-control enable surface |
| `SMART_PRE_RENDER` | Actual command/geometry evidence is bounded by existing adapter oracle | Public production EffectMain | Exact checkout request, preserve-RGB flag, result/max rectangles for fixed padded fixture |
| `SMART_RENDER` PF8 | Actual typed worker and preparation dependencies | Public production EffectMain | Exact padded-frame fixtures; checkout surface fixed |
| `SMART_RENDER` PF16 | Actual typed worker and preparation dependencies | Public production EffectMain | Exact padded-frame and extended-range fixtures; checkout surface fixed |
| `SMART_RENDER` PF32 | Actual typed worker and preparation dependencies | Public production EffectMain | Exact finite, tolerance, signed-zero, NaN/Inf/sNaN, subnormal and multicolor fixtures |

Largest remaining public-command gap: `ABOUT`. Its public branch is present, but the exact localized message depends on the DLL string-table initializer, which the current hostless AEX fixture does not execute.
