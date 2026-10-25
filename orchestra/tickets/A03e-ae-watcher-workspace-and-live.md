# A03e: watcher must ignore AE's main workspace window; then prove two unattended launches with the marker JSX

## Facts (A03d, `orchestra/reports/A03d-ae-crash-dialog-rule.md`)
- Two live launches: **no crash-recovery dialog** (the crash state is clean now) and a clean exit 0 both times. But the watcher classified the main untitled workspace window as `Unknown AE dialog` (window 1726, 3200×1743 points, title like `Adobe After Effects 2026 - 名称未設定プロジェクト *`). The test then stopped before the JSX could write its marker.
- The splash window vanishing during capture is already handled.

## Do
1. **Window classification.** Classify windows as follows:
   - main workspace windows (title starts with `Adobe After Effects 2026` and the window is large, e.g. at least 1000×600 points, or the AX role/subrole of a standard window when exposed): **not dialogs**, never clicked, never treated as unknown;
   - splash: ignored;
   - small, centred, modal-looking windows: candidate dialogs, under the existing rules.
   Add unit tests using A03b's `inspect-1609.png` and the A03d workspace capture as negative cases.
2. **Waiting for the JSX.** The e2e test must wait for the JSX marker (up to 3 minutes after the workspace appears) while the watcher keeps running, and only then expect `app.quit()`.
3. **Live proof.** Run the busy/lock/memory checks first. Then two launches in a row: prevent + scripting pref on → launch → marker written → clean exit, with no dialog clicks expected. Restore the scripting pref at the end. Record whether any dialog appeared.

## Rules
- Never SIGKILL or SIGTERM AE. Run one AE 2026 instance only, by full path. Do not run AE while the user's own AE is running.
- Make no plugin changes. Do not touch the release gate or ledger. The stop rule applies.
