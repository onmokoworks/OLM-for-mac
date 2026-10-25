# U02: KiraKira Effect Controls ramp editor: match the original (urgent, user priority)

## Why
- KiraKira is the only original with a drawable Effect Controls UI: five 310×170 "Ramp" editors, slots 14/20/26/32/38.
- The Mac port has a partial editor. U01 (`orchestra/reports/U01-custom-ui-survey.md`, "Event dispatch and KiraKira drawing/interaction" and "Mac feasibility") lists the differences:
  - strips are drawn with PaintRect instead of sampled stroked lines;
  - markers are white 5×10 instead of coloured 10×10 with theme frames;
  - nearest-stop selection instead of marker hit-testing;
  - no preset menu, copy/paste/randomize/flip, or ADJUST_CURSOR handling.

## Do
1. **Implement** the original's editor in `mac/OLMKiraKira/` exactly as U01 describes, using AE's cross-platform suites (EffectCustomUI, Drawbot Supplier/Surface/Path, App suite for theme colours and the colour picker, ParamUtils). This covers:
   - **Layout:** strip (10,5)-(202,55); markers 10×10 at `trunc(10+192*pos)`, y60-70; buttons copy/paste/randomize/flip at their rects and with their lowercase captions; the "▼  PRESETS" header and a 7-row preview list (64 presets from the original table at `1814d7030`, stride 0x144, row height 18, spacing 5).
   - **Drawing:** per-x stroked lines sampled at `(x-left)/width` including both endpoints; theme colours from AppGetColor roles 7/8/2/42, scaled ×1/65535; button state RGB factors ≈0.3/0.7 (use the exact float constants); default font size 11.0; antialias policy 0.
   - **Interaction:**
     - single click inserts a stop (fewer than 16 stops) using the sampled colour, then sorts;
     - clicking a marker selects it by hit-test;
     - a non-single click opens `PF_AppColorPickerDialog("Color select")`, where cancel keeps the old colour;
     - dragging clamps to [0,1]; more than 20 px below the strip gives a 0.5-alpha delete preview, and releasing there deletes the stop;
     - buttons arm on press and fire on release inside;
     - copy/paste use a buffer shared by the effect instance;
     - randomize changes RGB only, with the original hash pre-step and xorshift 13/17/5 global RNG;
     - flip reverses colour quadruples and keeps positions;
     - preset toggle/scroll/select copies the table entry into the clicked ramp;
     - ADJUST_CURSOR.
   - **Persistence:** keep the arbitrary-data contracts unchanged (NEW/COPY/DISPOSE/FLATTEN/UNFLATTEN/COMPARE/INTERP and the saved-project payload), and keep the render output unchanged. The KiraKira fuzz corpora must replay true.
2. **Separate logic from drawing** so it can be unit-tested: a pure state machine for events → payload changes, and a draw-command list builder. Write unit tests from U01's facts now.
3. **Compare against the original.** When U03's UI oracle exists (`~/.cache/olm-emu/worker-U03-ui/`, witnesses in `tests/ui_oracle/`), compare the payloads and ordered draw-call traces exactly. U03 is running in parallel: implement first, and if U03 has landed before you finish, run the comparison. Otherwise report "pending U03" — the orchestrator will run it.
4. **Check in real AE.** Build the bundle. Install only into scratch, not into the AE folders (A02b uses them). Real-AE visual checks happen later with the user.

## Acceptance
- Unit tests for every interaction listed above.
- Render unchanged: KiraKira default fuzz seed 1 n300 shows no exact→non-exact, and all KiraKira corpora replay true.
- Arbitrary-data flatten/unflatten round trip, byte-identical for all 64 presets.
- When U03 traces exist: payloads and draw traces equal to the original.

## Rules
- Use 1-2 processes. Change only KiraKira sources and plugin-only helpers. Do not touch the release gate or ledger. Commit partial results at least every 30 minutes. The stop rule applies.
