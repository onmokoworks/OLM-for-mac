# A01c: real-AE render matrix via a single GUI build step + aerender (continues A01/A01b)

## State (facts; read `orchestra/reports/A01-real-ae-smoke.md`, `A01b-real-ae-render-compare.md`, `tools/ae_smoke/README.md`)
- A01: AE 2026 loaded and applied all 10 bundles from `Plug-ins/OLM-smoke/`.
- A01b was blocked by modal dialogs:
  - crash recovery, caused by A01/A01b force-killing AE;
  - AE 2025 missing-plugin warnings for unrelated third-party plugins in `/Library/.../MediaCore`;
  - "scripting plugin not installed".
- The user has since launched AE 2026, chosen 続行, and quit it normally. AE is not running now.
- **Probable cause of the A01b confusion:** a dialog in the 2026 attempt referenced the AE **2025** Required dir.
  - Both versions share a bundle id, so `osascript tell application "After Effects"` or a bundle-id dispatch can reach the wrong version.
  - Never address AE by name or bundle id. Use only the full app path:
    - `"/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects" -r <jsx>`, or
    - `tell application "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app"`.
  - Use only one dispatch per launch. Do not fall back to a second dispatch while the first may still be pending.
- **AE 2025 is out of scope** for this ticket. Its startup warning repeats on every launch.

## Design
- **GUI AE is used only once per run.** One JSX does everything:
  - creates every comp for the whole matrix (no-effect I/O controls, plus effect cells), with params set;
  - adds output modules and render-queue items, with color management off;
  - saves `.aep` into scratch;
  - takes Effect Controls screenshots, if it is cheap to drive them from the script;
  - then calls `app.quit()`.
- **All renders go through `aerender -project <aep>`.** It is a command-line tool with no modals; its warnings go to stdout and get logged.
- **Never SIGKILL or SIGTERM AE.** If the JSX hasn't written its done marker within 3 minutes:
  1. take a `screencapture` (crop it to the dialog, at most 400 KB);
  2. try `osascript` (full app path) `quit` once;
  3. stop and report. Do not loop on retries.
- **Busy check:** match the main executable exactly (`MacOS/After Effects$`). If another AE is running, wait up to 2 h.

## Do
1. **I/O control.**
   - Render the no-effect comps for 8/16/32 bpc via aerender and compare them with the source pixels.
   - Fix the TIFF/EXR conversion until each round trip is exact: 16-bit 0..32768, straight vs premultiplied alpha, EXR channels.
   - Report the result.
2. **Matrix (AE 2026).** Cover the 10 plugins × 8/16/32 bpc, with the default params plus 3 exact corpus cases per plugin (`tests/fuzz_corpus/<plugin>/`).
   - Skip a case only when AE can't reproduce it, and give the reason.
   - Priority order: 8 bpc defaults for all 10, then the rest.
3. **Compare.**
   - Run the F47 native-plugin worker on the same bundle, input and params, and compare its output with AE's using `tools/ae_smoke/compare.py`.
   - Classify each difference: I/O conversion, color management, host/InData (downsample, ROI, Smart pre-render buffer expansion, pixel aspect and similar), or a plugin bug.
   - The scratch-only instrumented-bundle rule from A01b still applies.
3b. **Popup check.** A01b found source popup count/label mismatches in DirectionalBlur, DistanceGradation and KiraKira (`orchestra/reports/A01b-evidence/source-popups.json`).
   - Compare these with the original AEX PiPL and param registration: disassemble or trace the original `PF_ADD_POPUP` calls.
   - Use JSX to read what AE shows for these properties (number of choices, value range).
   - Classify each one as faithful to the original or a port bug. Report only; make no source changes.
4. **Single command.** `run_ae_smoke.py --year 2026 --stage build|render|compare|all` must reproduce everything. Document it in `tools/ae_smoke/README.md`.

## Rules
- At most one AE instance, and only one you started. Check `memory_pressure` (≥30% free).
- Make no plugin source changes, and do not touch the release gate or ledger.
- Leave the installed bundles in place.
- The stop rule applies. Partial results such as "I/O exact + 8 bpc defaults for 10 plugins" are valuable.
