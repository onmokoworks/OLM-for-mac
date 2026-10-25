# A03c: let AE scripts write files during runs, then prove an unattended AE launch twice

## Facts (A03b, `orchestra/reports/A03b-ae-crash-flags-and-ocr.md`)
- With `CrashOccurred` and `ForceQuitOccured` cleared, AE 2026 opened straight to the main workspace (`inspect-1609.png`): no recovery dialog seen. But the JSX marker was never written, and `app.quit()` never ran (the JSX writes the marker first).
- The orchestrator's check: the active prefs `~/Library/Preferences/Adobe/After Effects/26.3/Adobe After Effects 26.3 環境設定-indep-general.txt` have **no** `Pref_SCRIPTING_FILE_NETWORK_SECURITY` entry, so it is at its default off. A01 enabled it and then restored it. With it off, `new File(...).open("w")` fails, and AE may show a scripting warning.

## Do
1. **Scripting pref (user-approved for test runs).** Add a `prefs` step to `ae_dialog_watch`/`run_ae_smoke.py`, run only while AE is not running:
   - back up the prefs txt (copy plus hash);
   - set `"Pref_SCRIPTING_FILE_NETWORK_SECURITY" = 01` in the right section of `…環境設定-indep-general.txt` (find the section from A01's code/notes, or from AE 2026's own format; check `git log -S Pref_SCRIPTING` in this repo);
   - restore the original afterwards (`--restore`). Log before and after.
   Make the JSX defensive: wrap the marker write in try/catch and always call `app.quit()` in a finally block.
2. **Live proof, twice in a row.** Run the busy/lock/memory checks first. Then:
   prevent (crash flags) → prefs on → launch AE 2026 by full path with `-r` marker JSX → marker written → clean exit (no process, no signals) → crash flags still false.
   Then the second launch, the same way. Then restore the scripting pref, or leave it on if A02e follows immediately (record which). Keep the watcher running throughout, and record any dialog it saw or clicked.
3. If a dialog appears, the watcher handles it under the existing allowlist rules. Native-scale OCR must recognize the exact label; record what happened.

## Rules
- Never SIGKILL or SIGTERM AE. Run one AE 2026 instance only, by full path. Do not run AE while the user's own AE is running.
- Make no plugin changes. Do not touch the release gate or ledger. The stop rule applies.
