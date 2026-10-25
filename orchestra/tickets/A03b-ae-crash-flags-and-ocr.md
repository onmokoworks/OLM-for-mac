# A03b: clear AE's crash flags before launch, and make the OCR fallback read buttons reliably; prove both live

## Facts (A03, `orchestra/reports/A03-ae-dialog-watcher.md`)
- `~/Library/Preferences/com.Adobe.After Effects.26.3.plist` has `CrashOccurred = true` and `ForceQuitOccured = true` (sic). These are the most likely cause of the crash-recovery dialog: A01-A02d ended AE with timeouts/quit failures, never a clean quit.
- The watcher's Vision OCR on the A02d screenshot read the button as 繞行/統行 at confidence 0.3, because the capture was reduced.
- Accessibility and Screen Recording are both granted (`ae-dialog-watch permissions`). AE is not running now.

## Do
1. **Prevention (user-approved).**
   - Back up the plist: `defaults export` plus a file copy, into the ticket scratch with its hash.
   - Then set both keys false with `defaults write "com.Adobe.After Effects.26.3" CrashOccurred -bool false` and the same for `ForceQuitOccured`. Read them back with `defaults read`.
   - Make this a `prevent` step in `ae_dialog_watch`/`run_ae_smoke.py`: backup, set false, log the before/after values.
   - Touch only those two keys. Never delete prefs, projects or auto-saves.
2. **Live proof.** Run the busy/lock/memory checks first.
   - Launch AE 2026 by full path with a trivial JSX that writes a marker and calls `app.quit()`.
   - Expect no recovery dialog, the marker written, a clean exit, and the flags still false afterwards.
   - Repeat once to show it stays clean.
3. **OCR robustness.** Capture the AE window at native backing scale (Retina 2x) with ScreenCaptureKit (`SCStreamConfiguration` width/height = points × scale). Recognize with `.accurate` and language correction off.
   - Re-test on a fresh real crash-recovery screenshot if one appears.
   - Never accept a guessed label: exact allowlist match only, confidence ≥0.8.
   - If you can, reproduce the dialog safely. Do NOT force-kill AE. Instead set `CrashOccurred` back to true from the backup, then launch, then let the watcher click 続行. Verify the click and the clean quit afterwards.
4. Update `tools/ae_smoke/README.md` with the unattended procedure.

## Rules
- Never SIGKILL or SIGTERM AE. Run one AE 2026 instance only, by full path. Do not run AE while the user's own AE is running.
- Make no plugin changes. Do not touch the release gate or ledger. The stop rule applies.
