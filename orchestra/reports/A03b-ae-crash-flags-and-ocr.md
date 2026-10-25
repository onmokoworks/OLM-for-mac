status: blocked
summary: Implemented authorized two-key prevention with export/copy backups and readback.
  Native backing-scale capture and accurate OCR with language correction off are implemented.
  One live launch captured 2x, then capture timed out; JSX marker absent.
  Normal quit timed out, but AE subsequently disappeared without signals.
  Watcher 12/12 and pipeline 6/6 pass; two clean launches/live button click remain unproven.

facts:
- Branch: `orch/A03b-ae-crash-flags-and-ocr`. Read AGENT_GUIDE, compatibility
  plan and A03 report. No plugin, ledger, release gate, MAIN or emulator edits.
- Preflight via `run_ae_smoke.running`, `screen_locked`, `preflight`: no AE,
  unlocked console, memory free 37%. Checks repeated by E2E before dispatch.
  `ae-dialog-watch permissions`: Accessibility=true, Screen Recording=true.
- Prevention uses `defaults export com.Adobe.After Effects.26.3 <backup>`,
  `shutil.copy2` of the original plist, and hashes both **before** writes.
  Actual export SHA-256:
  `27dd406cd2507cddaf9be51bfe5b02ef1de780497a3a3af01205e0edfc6b9a20`.
  Actual file-copy SHA-256:
  `205713a9b78e8c7e4d3a3955f4791f9c3d2efc24106e0c8359a15f557b017a2a`.
  Backups remain in ticket scratch under
  `e2e/first-clean-launch/dialogs/preferences-1792923982507167000/`.
  Full backup paths/hashes and before/after values are committed in
  [prevention.json](A03b-evidence/prevention.json); private preference payloads
  remain in scratch, as requested.
- Executed exactly these preference writes, once each:
  `defaults write "com.Adobe.After Effects.26.3" CrashOccurred -bool false`
  and `defaults write "com.Adobe.After Effects.26.3" ForceQuitOccured -bool false`.
  `defaults read` before returned `1` for both, after returned `0` for both.
  Final reads after AE disappeared also returned `0` for both.
  No other keys, projects or auto-saves were changed by this worker.
- Live command (exit 1):
  ```sh
  PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py \
    --scratch orchestra/state/A03b-ae-crash-flags-and-ocr/e2e \
    --binary orchestra/state/A03b-ae-crash-flags-and-ocr/build/ae-dialog-watch \
    > orchestra/state/A03b-ae-crash-flags-and-ocr/e2e.log 2>&1
  ```
  One full-path `/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects -r <launch.jsx>`
  dispatch, PID **59462**. Watcher AXObserverCreate result 0; two captures of
  window 1607 at 766×516 points, scale 2, **1532×1032 pixels**.
  Then first failure: **ScreenCaptureKit capture timeout**. The live binary's
  inherited error wording mentioned Screen Recording; final code removes that
  unsupported diagnosis. No permission rejection occurred.
- Failure inspection captured window 1609, title
  `Adobe After Effects 2026 - 名称未設定プロジェクト *`, at 3200×1743 points,
  scale 2, **6400×3486 pixels**, with OCR output retained. Image SHA-256:
  `4d937c907d7d1ba97d10cd3af426838ee097eeecac70180817d22412361d7855`.
  [Native PNG](A03b-evidence/inspect-1609.png),
  [capture/OCR](A03b-evidence/blocked-capture.jsonl),
  [watcher events](A03b-evidence/dialogs.jsonl).
  Visual inspection shows the empty main workspace, not a recovery dialog.
  This does not prove no dialog appeared earlier.
- No JSX marker, no click events, no before/after click pairs, no second launch.
  Failure handler sent normal full-path Apple-event quit once. That request
  timed out after 20 seconds; AE still existed at the test's final-process check.
  A later read-only `ps` check found PID 59462 absent; `running()` returned [].
  [Final state](A03b-evidence/final-state.json) distinguishes this later observation
  from [E2E final processes](A03b-evidence/final-processes.json).
  No SIGKILL/SIGTERM, second quit request or deliberate recovery-flag reset to
  true was used. No AE or watcher process remains.
- Final offline commands below: Swift compilation exit 0, watcher **12/12**,
  pipeline **6/6**; `git diff --check` passes. Added tests verify backup ordering,
  exact write scope/readback, preserved unrelated key, and busy refusal.
  Existing tests retain low-confidence/forbidden-overlap/exact-label checks and
  saved A02d OCR fixture. No fresh recovery screenshot was obtained.
- Helper now derives dimensions from SCContentFilter contentRect × pointPixelScale;
  recognizes `.accurate`, Japanese/English, language correction **off**, no custom
  words. PNG evidence preserves the native pixels passed to Vision. The existing
  exact allowlist and confidence ≥0.8 are unchanged. No guessed aliases added.
- Scratch stayed below 5 GiB (89 MiB before cleanup). Regenerable build binary and
  module cache removed after tests; logs/backups retained. AE's installed plugin
  logged a hard-coded `/tmp/nexpression_bridge_59462.sock`; this worker did not
  create scratch files there or modify the plugin. Test TMPDIR/TMP/TEMP pointed
  to ticket scratch.

inference:
- Clearing flags is demonstrated, but their causal prevention effect is not:
  only a short startup interval was monitored before capture failed.
- The initial small window was plausibly the splash, and capture may have raced
  its disappearance. This is an untested hypothesis, not a diagnosed permission
  failure; the later main-window capture and granted permissions argue against
  assuming a persistent TCC problem.
- Missing JSX execution and delayed shutdown remain separate unresolved host
  lifecycle boundaries. AE disappearance after the quit request does not establish
  successful `app.quit()` or a clean executable exit.
- Stopped live testing on the first failed launch/quit boundary. Did not risk a
  second instance or manufacture recovery while clean lifecycle was unproven.

changed_files:
- `tools/ae_smoke/ae_dialog_watch/watcher.py`
- `tools/ae_smoke/ae_dialog_watch/main.swift`
- `tools/ae_smoke/ae_dialog_watch/test_watch.py`
- `tools/ae_smoke/ae_dialog_watch/test_e2e.py`
- `tools/ae_smoke/ae_dialog_watch/README.md`
- `tools/ae_smoke/run_ae_smoke.py`
- `tools/ae_smoke/README.md`
- `orchestra/reports/A03b-ae-crash-flags-and-ocr.md`
- `orchestra/reports/A03b-evidence/` (logs, native screenshot, hashes)

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py \
  --scratch orchestra/state/A03b-ae-crash-flags-and-ocr/recheck \
  > orchestra/state/A03b-ae-crash-flags-and-ocr/recheck.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py \
  > orchestra/state/A03b-ae-crash-flags-and-ocr/recheck-pipeline.log 2>&1
git diff --check
```
Expected: 12 watcher tests, 6 pipeline tests, whitespace check pass. macOS/Swift
required, pipeline needs numpy. These commands do not launch AE or modify prefs.
Live E2E command above requires fresh scratch and prior lifecycle investigation;
its observed result is blocked, not an expected successful verification.

next:
- Investigate ScreenCaptureKit timeout across splash-to-workspace transition;
  preserve timeout/window lifetime evidence without presuming permission failure.
- Investigate why full-path `-r` never produced the trivial JSX marker and why
  normal quit was delayed. Then repeat prevention test twice with markers,
  exit-code 0, no dialogs/clicks, and false flags after each exit.
- Only after clean lifecycle proof, attempt authorized flag-only recovery
  reproduction (CrashOccurred true from backup), capture fresh native dialog,
  prove exact 続行 confidence ≥0.8, verified click and clean quit; never force kill.
- Preserve scratch preference backups before deleting this worktree. No durable
  emulator/reference worker or oracle bundle was produced by this ticket.
