# U01: survey the original plugins' custom Effect Controls UI (urgent, user priority)

## Why
- The Windows originals have custom UI in the Effect Controls panel (custom preview drawing, click interactions, dynamic labels). The Mac port has none and does not advertise the capability (old `KNOWN_LIMITATIONS`: "custom preview / click / dynamic label EVENT/UPDATE paths not ported").
- This is the only user-visible feature gap left. The user wants it ported, matching the original's look and behaviour.

## Do (survey only; implementation tickets follow)
For each of the 10 originals (`plugins_2025/*.aex`, decomp in `decomp/*.aex.c.txt`):
1. **Capabilities.**
   - PiPL and GlobalSetup out_flags: `PF_OutFlag_CUSTOM_UI`, `PF_OutFlag_SEND_UPDATE_PARAMS_UI`, and `PF_OutFlag2_*`;
   - params with `PF_PUI_CONTROL`, `PF_PUI_ECW_SEPARATOR` or custom UI widths/heights (`PF_CustomUIInfo`, `ui_width/ui_height`);
   - which `PF_Cmd_EVENT` events are handled (`PF_Event_DRAW`, `DO_CLICK`, `DRAG`, `ADJUST_CURSOR`, `NEW_CONTEXT`...) and in which contexts (ECW, comp, layer).
2. **Behaviour.** From the disassembly, for each handled event, describe:
   - what is drawn: shapes, colours, text, previews of the effect (e.g. a gradient strip, a curve, colour swatches), and which Drawbot/DRAWBOT or Win32 GDI calls are used;
   - what clicks or drags do: which params change, and how;
   - `PF_Cmd_UPDATE_PARAMS_UI`: which params get renamed, enabled/disabled or hidden, under which conditions. Include the dynamic label strings.
   Cite addresses. If a plugin draws through a Windows-only API (GDI), say so: the Mac port must use the AE Drawbot suites.
3. **Mac feasibility.** For each item, map it to the AE SDK Mac APIs (Drawbot suites, `PF_EffectCustomUISuite`, `PF_ParamUtilsSuite`, `AEGP_DynamicStreamSuite` for hiding). Estimate the effort. Note anything AE on macOS cannot do the same way.
4. **Verification plan.**
   - Logic (which params change on click, which labels appear when) can be tested hostlessly against the original on the emulator, if AEXCompat can dispatch `PF_Cmd_EVENT` and `UPDATE_PARAMS_UI` (check, and report what AEXCompat would need).
   - Drawing can be compared by recording Drawbot call sequences.
   - Final visual check in real AE.
5. **Write** `orchestra/reports/U01-custom-ui-survey.md`:
   - a per-plugin table (custom UI yes/no, events, draws, click semantics, dynamic labels, effort);
   - in `next`, implementation tickets ordered by user value (most visible first).

## Rules
- Read-only investigation: make no plugin source changes. Use 1-2 processes. Commit partial results at least every 30 minutes. The stop rule applies.
