status: blocked
summary: Added Swift CGWindow/AX/Vision watcher and Python build-stage integration.
  Offline watcher tests 10/10 and existing pipeline tests 6/6 pass.
  One prevention-disabled real launch timed out without a JSX marker; clicks 0.
  Initial watcher exited prematurely; subsequent lifecycle fix is offline-tested only.
  No deterministic prevention switch, live click, or clean second-launch proof established.

facts:
- Branch `orch/A03-ae-dialog-watcher`. Read AGENT_GUIDE, A02b ticket/dialog update,
  A02d report/image, smoke runner/docs, compatibility plan and emulator guidance.
  No plugin source/bundle, ledger, release gate, MAIN or emulator modification.
- Before inspecting settings, copied 66 files / 4,436,530 bytes from the `26.*`
  preference directories to ticket scratch. Separately backed up nearby plists
  and the actual `~/Library/Logs/Adobe/Adobe After Effects 2026` directory (ten
  zero-byte UXP logs). Initial backups remain in scratch; no restoration is
  needed because **no setting, project or auto-save was modified/moved**.
- Backup of `com.Adobe.After Effects.26.3.plist` has SHA-256
  `3f4b8f6cc412b5312e8e97724f255498e520497d4c5c2112890e518e652b0802`.
  Its on-disk `CrashOccurred` and `ForceQuitOccured` are both Boolean true.
  These values were not proven equivalent to effective CFPreferences or a
  deterministic launch trigger. Text prefs did not yield a confirmed home-screen
  suppression key. `SCRPriorState.json` contained a `last_match_job` ID, not a
  demonstrated recovery switch. MRU references to crash projects were left alone.
- Final prevention function exports the effective version-specific domain to a
  durable backup **before** inspecting candidate flags, logs hashes and
  `changes: []`, and performs no writes to AE preferences. This is the ticket's
  permitted no-safe-deterministic-switch fallback, not successful prevention.
- `ae-dialog-watch permissions`: Accessibility=true, Screen Recording=true;
  [permissions](A03-evidence/permissions.json). No tool permission rejection.
- Native helper uses CGWindow owner PID/layer/title/bounds, AXObserver,
  ScreenCaptureKit window+PID filtering, ja/en Vision OCR, matching-window
  AXPress or foreground/occlusion-checked PID-directed mouse events. Policy
  requires known context, exact allowlist, confidence, valid geometry and no
  forbidden-box overlap. It records before/after window PNGs <=400 KB and JSONL,
  verifies disappearance, caps clicks at ten, and stops on unknown/ambiguous UI.
  These code paths are **implemented, not live-proven**.
- Offline fixture: `ae-dialog-watch ocr orchestra/reports/A02d-evidence/blocked.png`.
  Image SHA-256 `b3f107159d676570bb4899a357cb9f70d9fe29d4863562706d184170ba68d04b`.
  Vision recognized `クラッシュ修復オプション`, but the reduced button text as
  `繞行` (confidence 0.3), then `統行` (0.3) with language correction/custom words.
  Neither became an allowlisted candidate. The dictionary hypothesis did not
  recover that label; no fuzzy alias/coordinate workaround was added.
  [original OCR](A03-evidence/a02d-ocr.json), [corrected OCR](A03-evidence/a02d-ocr-corrected.json).
- Final compiler: Apple Swift 6.2.4; compile exit 0, no diagnostics.
  `PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py
  --scratch orchestra/state/A03-ae-dialog-watcher/final-build`: **10/10 pass**.
  Includes exact allowlist, destructive overlaps, negative-origin centre,
  low confidence/invalid boxes, context, saved A02d image, disabled prevention,
  premature exit, error exit and cooperative shutdown.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py`: **6/6 pass**.
  Python AST parse and `git diff --check` pass. Tests are not AE render results.

real_attempt:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py \
  --scratch orchestra/state/A03-ae-dialog-watcher/e2e \
  --binary orchestra/state/A03-ae-dialog-watcher/ae-dialog-watch \
  > orchestra/state/A03-ae-dialog-watcher/e2e.log 2>&1
```
- One full-path AE 2026 dispatch, owned PID **54019**. Prevention disabled;
  no crash flag deliberately set/cleared, no crash manufactured. Before launch:
  no AE/aerender, absent lock key in logged-in on-console session = unlocked;
  final memory preflight **59% free** (retained memory log has trailing whitespace normalized). Checks were repeated immediately before
  dispatch. [preflight/evidence](A03-evidence/pending-recovery/).
- Initial helper logged AXObserverCreate result **0**, then `stopped`, clicks **0**,
  while `ps` still showed PID 54019. It had not enumerated/captured any window.
  The initial Python code accepted that zero exit too readily. Final code now
  binds liveness to the executable path (`proc_pidpath`), tolerates app
  registration absence for at most ten seconds, and rejects helper success-exit
  while the owned AE executable is still present. **This fix was not re-launched.**
- Read-only Swift probe during that same launch found one CG window **1522**,
  layer **0**, bounds **x=0, y=25, width=3200, height=1743**, titled
  `Adobe After Effects 2026 - 名称未設定プロジェクト *`.
  [probe](A03-evidence/probe.log). This was a main project window, not proof that
  recovery never appeared earlier. Subsequent inspect produced no captured
  image; the final inspection after quit rejected the absent owned process.
- JSX marker **absent** after **180-second** deadline; test exited **1**.
  Normal full-path `osascript ... quit` sent once, quit log empty; AE main process
  subsequently absent. No SIGKILL/SIGTERM, global keystroke, other-app interaction,
  or second launch. [failure log](A03-evidence/e2e.log),
  [final processes](A03-evidence/final-processes.json).
- Live AX clicks **0**, OCR clicks **0**, before/after click screenshot pairs **0**,
  successful JSX runs **0**, clean-second-launch tests **0**. No timeout screenshot
  was successfully retained in this attempt. The revised test captures the owned
  window on failure before its one normal quit request. No live capture-permission
  failure was established; this is not a request for another TCC grant.

inference:
- Premature watcher exit plausibly arose from transient NSRunningApplication
  identity/registration state; its exact cause is unproven. Executable liveness
  and Python fail-closed checks address the observed failure boundary.
- The missing JSX marker is a separate unresolved startup/dispatch boundary.
  The main-window probe alone cannot establish why the script did not run or
  whether a recovery prompt had appeared. Do not attribute this to a plugin bug.
- The old reduced screenshot is inadequate for a positive OCR click proof;
  native window capture may improve recognition but that remains unmeasured.
- Stopped after the failed real attempt; did not loop through more launches or
  fabricate pending recovery. This ticket is blocked on live lifecycle/dispatch
  investigation and evidence, not declared done because offline tests pass.

changed_files:
- `tools/ae_smoke/ae_dialog_watch/{Policy.swift,main.swift,__init__.py,watcher.py,test_watch.py,test_e2e.py,README.md}`
- `tools/ae_smoke/run_ae_smoke.py`, `tools/ae_smoke/README.md`
- `orchestra/reports/A03-ae-dialog-watcher.md`, `orchestra/reports/A03-evidence/`

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py \
  --scratch orchestra/state/A03-ae-dialog-watcher/recheck
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py
git diff --check
```
Expected: native compile succeeds; watcher 10 tests, pipeline 6 tests pass;
whitespace check succeeds. macOS with Swift/Vision required; pipeline needs numpy.
No AE launch. Regenerable binaries/module caches were removed after verification.

next:
- A03 follow-up: verify executable-scoped watcher survives AE registration, then
  investigate the full-path `-r` JSX dispatch/marker boundary with all the same
  busy/lock/memory rules. Use fresh scratch, one dispatch and one normal quit;
  do not restore old flags or manufacture a crash.
- Obtain actual window captures and positive live OCR `続行` / AXPress evidence,
  disappearance captures, JSX marker + `app.quit()` and a subsequent recovery-free
  launch. Review localized context fixtures before broadening dialog recognition.
- Investigate effective crash/home settings only from backups; current default
  does not suppress recovery by modifying user preferences. No other ticket's
  plugin/render work is advanced by this attempt.

cleanup:
- No AE, aerender or watcher process remains. Scratch was 242 MiB before cleanup,
  below 5 GiB (4.7 MiB after cleanup); regenerable compiler module caches and native executables removed.
  Logs/backups retained, evidence committed. No push, stash or history rewrite.
