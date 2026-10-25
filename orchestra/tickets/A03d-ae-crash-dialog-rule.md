# A03d: crash-recovery dialog rule (layout-anchored 続行), find AE's real crash marker, prove two unattended launches

## Facts (A03c, `orchestra/reports/A03c-ae-scripting-pref-and-live-proof.md`, `A03c-evidence/no-safe-button-1670.png`)
- With `CrashOccurred` and `ForceQuitOccured` both false, AE 2026 still showed **クラッシュ修復オプション**. So AE also tracks the crash state somewhere else.
- The dialog has one row of 4 pill buttons, left to right: **続行** (default, white outline), **プラグインを管理**, **環境設定をリセット**, **セーフモードで開始**. Vision reads the title and the other three labels correctly, but misreads 続行 (綂行/繞行/統行, conf 0.3).

## Do
1. **Dialog-specific rule** in `ae_dialog_watch`, used for this exact dialog only. All of these must hold:
   - the OCR title is exactly `クラッシュ修復オプション` with high confidence;
   - the OCR finds the exact labels `プラグインを管理`, `環境設定をリセット` and `セーフモードで開始` on one horizontal row;
   - exactly one more text box exists on that row, left of `プラグインを管理`, with nothing overlapping it.
   Then click the centre of that leftmost box (the 続行 button). Log it as `rule=crash_recovery_layout`. Never click if any condition fails. Never click the other three.
   Add unit tests on the A02d and A03c screenshots, plus negative variants: a missing label, an extra box, swapped positions, a different title.
2. **Find AE's real crash marker.** Before the next launch, snapshot (paths, mtimes, sizes, hashes) of:
   - `~/Library/Preferences/Adobe/After Effects/26.3/`;
   - `~/Library/Application Support/Adobe/After Effects/26.3/` (and `Common`);
   - `~/Library/Preferences/com.Adobe.After Effects.26.3.plist`;
   - `~/Library/Caches/Adobe/After Effects/26.3/`.
   Compare it after a clean quit, and after the dialog appears. Identify the file or key that encodes "previous session crashed". Document it. If it is clearly a marker, also clear it (after a backup) in the `prevent` step.
3. **Live proof.** Run the busy/lock/memory checks first. Launch (with prevent + scripting prefs on) → if the dialog shows, the watcher clicks 続行 by the rule → the marker JSX runs → `app.quit()` → clean exit. Then launch a second time: expect no dialog, the marker written, and a clean exit. Restore the scripting pref at the end, unless the next step uses it immediately; record which.

## Rules
- Never SIGKILL or SIGTERM AE. Run one AE 2026 instance only, by full path. Do not run AE while the user's own AE is running.
- Never click `環境設定をリセット`, `セーフモードで開始` or `プラグインを管理`.
- Make no plugin changes. Do not touch the release gate or ledger. The stop rule applies.
