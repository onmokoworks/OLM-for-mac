# A03: automatic AE dialog handling: prevent the crash-recovery dialog, and click allowlisted buttons even when AE hides them from Accessibility

## Why
- The user wants real-AE runs to be fully unattended. A02d (`orchestra/reports/A02d-real-ae-retest-downsample.md`, `A02d-evidence/`) launched AE 2026, which stopped at the **crash-recovery dialog** ("続行" visible in the screenshot).
- AE draws that dialog with its own UI toolkit, so System Events / AX saw **zero windows and zero UI elements**, even with Accessibility granted to Terminal and osascript. That grant is confirmed: `AXIsProcessTrusted()` is true from this session.
- AE is not running now.

## Do
Build `tools/ae_smoke/ae_dialog_watch/`: a small Swift command-line tool plus a Python wrapper used by `run_ae_smoke.py`.
1. **Prevent.** Find out what makes AE 2026 show crash recovery on the next launch, and clear that condition safely before each launch.
   - Inspect only after taking a backup: `~/Library/Preferences/Adobe/After Effects/26.*`, the crash or recovery files near it, and the AE logs.
   - Typical candidates are an unclean-exit marker or flag in the prefs, and auto-save/recovery folders.
   - Document exactly what you change. Back up any file before editing it. Never delete the user's projects or auto-saves; move them to a backup folder instead.
   - If you cannot find a safe deterministic switch, say so and rely on step 2.
   - Also consider prefs that suppress the start/home screen.
2. **Detect.** Do this at OS level, scoped to the AE 2026 process, which is identified by its full bundle path and PID.
   - Use `CGWindowListCopyWindowInfo` to notice new AE windows: owner PID, layer, bounds, title.
   - Use `AXObserver` for windows that AX exposes. Use AX `AXPress` on allowlisted buttons when they are exposed.
   - For dialogs AX cannot see, capture the window (`CGWindowListCreateImage` / ScreenCaptureKit) and run **Vision OCR** (`VNRecognizeTextRequest`, languages ja and en) to find allowlisted button labels. Then click the centre of the recognized text box with `CGEvent` mouse down/up, after bringing AE frontmost.
   - Verify the result: the dialog must disappear in the next capture.
3. **Allowlist and safety.** Use the same lists as `orchestra/tickets/A02b-real-ae-retest-downsample.md`, "Dialog handling update": allowed `OK, 続行, Continue, 閉じる, Close, 後で, Later, スキップ, Skip, 今はしない, Not Now`, never the destructive ones.
   - Never click a label whose recognized box overlaps a never-click label in the same dialog.
   - Before and after each click, save a cropped screenshot (≤400 KB) and a JSONL record: time, PID, window bounds, OCR text, chosen label, method AX or OCR.
   - Allow at most 10 clicks per AE launch. An unknown dialog means stop and report.
   - Never send keystrokes globally. Never touch other apps.
4. **Integrate.** `run_ae_smoke.py --stage build` starts the watcher before launching AE and stops it after AE quits.
5. **Test.** Prove each path:
   - unit tests for the allowlist, overlap and box-centre logic, using saved screenshots, including A02d's crash-recovery screenshot;
   - one real end-to-end: launch AE 2026 by full path with the prevention step disabled, so that crash recovery appears if it is still pending; let the watcher click 続行; run a trivial JSX that writes a marker and calls `app.quit()`; confirm a clean quit (no AE process), and that the next launch shows no recovery dialog.
   - Check the busy/lock/memory preconditions first, exactly as in A02b-d (absent `CGSSessionScreenIsLocked` = unlocked).

## Rules
- Never SIGKILL or SIGTERM AE. Run one AE instance only, and only AE 2026, by full path. Do not run AE while the user's own AE is running.
- Screen Recording permission may be needed for window capture. If capture returns only wallpaper or blank, or fails, stop and report `blocked: needs Screen Recording for Terminal`.
- Make no plugin changes. Do not touch the release gate or ledger. Commit partial results at least every 30 minutes. The stop rule applies.
