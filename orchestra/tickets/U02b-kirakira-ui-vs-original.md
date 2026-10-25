depends: U02-kirakira-ramp-editor
# U02b: KiraKira ramp editor: exact comparison against the original via the U03 UI oracle

## Facts
- U02 (merged) implemented the ramp/button/preset state machine, a draw-command builder and the AE adapter.
- U03 (merged) delivered the UI-session oracle: worker `~/.cache/olm-emu/worker-U03-ui/`, witnesses in `tests/ui_oracle/` (17 sessions, 174 dispatches), recording Drawbot/CustomUI/App suites.

## Do
- Build a Mac-side UI test host that runs the same sessions through the Mac KiraKira EVENT handler, with the same injected theme colours, fonts, scale, picker results and RNG state, and records the same canonical JSON: payload before/after, param changes, and the ordered draw-call trace.
- Compare every KiraKira witness session exactly. Fix every difference in the Mac implementation: layout, colours, line sampling, markers, text, hit tests, drag/delete, picker, buttons, presets, RNG.
- Add more oracle sessions as needed to cover U01's test matrix (0/1/16 stops, boundaries ±5, y offsets 20/21, menu scroll first/last, copy across ramps, randomize ×2).
- Note U03's "inactive serialization-tail differences". Classify them faithfully, and keep the saved-project payload compatible.

## Acceptance
- All KiraKira UI sessions are equal to the original: payloads and draw traces.
- Render unchanged: KiraKira default fuzz seed 1 n300, all corpora, and `ref_vs_fast`.

## Rules
- Use 1-2 processes. Change only KiraKira sources and the test host. Do not touch the release gate or ledger. The stop rule applies.
