# U03: AEXCompat UI-session oracle: run the original's PF_Cmd_EVENT and UPDATE_PARAMS_UI and record the results

## Why
- `orchestra/reports/U01-custom-ui-survey.md`, section "Verification plan: what AEXCompat needs", explains what is missing:
  - the Unicorn guest has no UI event dispatch and no Drawbot recording;
  - the native minihost hard-codes ECW index 1 and lacks Drawbot Supplier slot 4, Surface slots 9/13, etc.
- U02 (KiraKira ramp editor) and U04/U05 (dynamic controls) need the original's exact event results and drawing calls to be bit-exact with the original UI logic.
- The user allows **direct changes to AEXCompat** (`~/Documents/Projects/Personal/04_Tools/AEXCompat`).

## Rules for AEXCompat (same as F54)
- Read `AGENTS.md` and `CLAUDE.md` there and follow their technical rules: focused behavioural tests, Release build + self-test, a local review loop.
- Do NOT post claim comments, push or open PRs. Write the claim text and the PR body into the report for the user.
- Work in your own worktree:
  `git -C ~/Documents/Projects/Personal/04_Tools/AEXCompat worktree add ~/Documents/Projects/Personal/04_Tools/AEXCompat-olm-U03 -b olm/U03-ui-session origin/main`
- Do not touch the main worktree or other worktrees, including F54's `AEXCompat-olm-F54`. Never rebuild a registered worker in place. Install the new one to `~/.cache/olm-emu/worker-U03-ui/` with an INDEX entry.

## Do
Implement U01's plan items 1-5 in the Unicorn guest, as an explicit UI-session mode (render mode unchanged):
1. **Setup and state.**
   - Run the original's GlobalSetup and ParamsSetup, plus arbitrary-data initialization through the original callbacks.
   - Accept the exact param slot, CONTROL area, current frame, x/y, click count, drag sequence/final flag and context.
   - Keep state across events, including the shared copy buffer and the RNG state.
2. **UPDATE_PARAMS_UI.** Allow explicit `PF_Cmd_UPDATE_PARAMS_UI` (cmd 14) dispatch for handler-logic tests. Capture:
   - `PF_UpdateParamUI` changes (UI flags such as DISABLED);
   - DynamicStream HIDDEN flags, using the real ID→slot mapping;
   - any name writes.
   Implement the PF Interface/Stream/Effect handle lifetimes and the current time the older plugins use.
3. **ABI.** Marshal the Win64 EventExtra exactly, per U01's ABI notes: PF_Point ordering, the 5th/6th stack arguments, coordinate frames.
4. **Recording suites.** Provide recording Drawbot (Supplier including `NewDefaultFont`, Surface including `DrawString` and `SetAntiAliasPolicy`, Path), CustomUI and App suites:
   - theme `GetColor` with injectable values;
   - picker accept/cancel with an injectable colour;
   - invalidation.
   Record ordered calls with exact float bits, strings, rects/paths, stable object IDs and retain/release. Fail closed on any unsupported suite call.
5. **Output.** Write canonical JSON per event: the arbitrary payload before/after, param/UI mutations, and the ordered draw-call trace.
6. **Witnesses.** Produce a starter set and commit it under OLM `tests/ui_oracle/`:
   - KiraKira: draw default ramp; click-insert; marker select; drag; drag-delete at y+20/+21; picker accept/cancel; copy/paste between two ramps; randomize with a fixed RNG state; flip; preset menu open/scroll/select;
   - UPDATE matrix rows for ColorKeep, ColorKey, Smoother2, DirectionalBlur, RadialBlur, DistanceGradation and Blur, as listed in U01.
7. **Report** `orchestra/reports/U03-aexcompat-ui-oracle.md` with:
   - the AEXCompat branch and SHA;
   - the tests run;
   - the CLI usage;
   - the witness list;
   - the draft claim/PR text.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free) before Rust builds, and delete build trees afterwards.
- Make no OLM plugin source changes.
- Commit partial results at least every 30 minutes. The stop rule applies. Getting the KiraKira draw-and-click traces plus the UPDATE capture for 2 plugins working is already a success.
