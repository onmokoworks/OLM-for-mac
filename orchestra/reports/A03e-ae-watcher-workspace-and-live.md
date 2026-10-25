status: done
summary: Workspace metadata now bypasses dialog OCR/buttons; 16 watcher tests pass.
  E2E waits up to 180 seconds for JSX after workspace detection, then 60 seconds for quit.
  A -r-only attempt timed out; one DoScriptFile dispatch after workspace fixed the probe.
  Two consecutive unattended launches wrote markers and exited 0 with zero clicks.
  All scripting preferences restored byte-exactly; no AE remains.

facts:
- Read AGENT_GUIDE.md, compatibility plan, A03d report, ticket and watcher sources.
  Branch orch/A03e-ae-watcher-workspace-and-live. No plugin, gate, ledger, MAIN,
  external emulator, or production smoke-runner changes. No signals sent to AE.
- Offline command below: 16 watcher tests pass, including A03b inspect-1609.png,
  A03d window 1726 metadata/OCR, title/size/AX/modal boundaries and wait phases.
  A03d's workspace PNG is absent from all available project checkouts; its committed
  dialogs.jsonl preserves the real 3200x1743 window and OCR used by this regression.
  Preference tests: 3 pass. Pipeline tests: 6 pass. git diff --check passes.
- Initial preflight: no AE, screen unlocked, memory free 44%. Each live launch
  repeated busy/lock/memory checks. Full-path AE 2026 executable only, one instance.
- Initial live command (exit 1):
  PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py --scratch orchestra/state/A03e-ae-watcher-workspace-and-live/live --binary orchestra/state/A03e-ae-watcher-workspace-and-live/build/ae-dialog-watch
  PID 69208, workspace 1745 recognized, no marker after the full post-workspace
  180 seconds. Cleanup requested normal quit; a save-changes dialog 1759 appeared
  and was rejected as unknown with no click. AE exited 0. No recovery dialog.
  This attempt used the previous -r dispatch; it is retained as failure evidence.
- Installed Contents/Resources/ae.sdef declares DoScriptFile (miscfile). The e2e
  probe now starts without -r, verifies the owned PID is the sole AE, and submits
  exactly one DoScriptFile event by full app path after workspace detection.
  It keeps the watcher running during dispatch, marker waiting and quit.
- Successful command (exit 0; stdout retained in A03e-evidence/live-dispatch.log):
  PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py --scratch orchestra/state/A03e-ae-watcher-workspace-and-live/live-dispatch --binary orchestra/state/A03e-ae-watcher-workspace-and-live/build/ae-dialog-watch
  Consecutive PIDs 70811 and 70889 each wrote exactly
  `A03c JSX executed; scripting=1`, exited 0 through JSX app.quit(), and left []
  AE processes. Both results: workspace_seen=true, dialog_events=0, clicks=0,
  CrashOccurred=0, ForceQuitOccured=0. Cleanup quit_requested=false for both.
  PID 70811 briefly exposed a `終了する準備` (preparing to quit) window; neither
  successful run exposed a recovery/save/unknown candidate dialog.
- All three scripting records: restored=true; original/restored SHA-256
  bb437dbab0b979e92fb55e33051d9331d12f1fc86bb64e33aee8dd16dad77f03.
  Logs, inventories, preference backups, markers, captures and SHA-256 manifest
  retained in orchestra/reports/A03e-evidence/. Final running processes [].
  Scratch was 89 MiB before cleanup; regenerable Swift binary/module cache removed.
  No worker-started background process remains. Worker temporary paths were inside
  ticket scratch; installed third-party extension logs mention its own /tmp socket.

inference:
- Window metadata removes dependence on unreliable workspace panel OCR, before
  any dialog context or button checks can run. Explicit AX modal windows remain
  dialog candidates and unknown candidates still fail closed.
- The -r-only failure establishes missing marker execution in that launch, not
  a general explanation of AE's CLI behavior. Explicit post-workspace dispatch
  is supported by the installed dictionary and proved twice here.
- These runs prove the e2e marker lifecycle, not live recovery-button correctness
  or production smoke-runner dispatch (the latter still uses -r).

changed_files:
- tools/ae_smoke/ae_dialog_watch/Policy.swift
- tools/ae_smoke/ae_dialog_watch/main.swift
- tools/ae_smoke/ae_dialog_watch/test_e2e.py
- tools/ae_smoke/ae_dialog_watch/test_watch.py
- tools/ae_smoke/ae_dialog_watch/README.md
- orchestra/reports/A03e-ae-watcher-workspace-and-live.md
- orchestra/reports/A03e-evidence/

verify:
```sh
mkdir -p orchestra/state/A03e-ae-watcher-workspace-and-live/recheck
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py --scratch orchestra/state/A03e-ae-watcher-workspace-and-live/recheck > orchestra/state/A03e-ae-watcher-workspace-and-live/recheck-watch.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_prefs.py orchestra/state/A03e-ae-watcher-workspace-and-live/recheck > orchestra/state/A03e-ae-watcher-workspace-and-live/recheck-prefs.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py > orchestra/state/A03e-ae-watcher-workspace-and-live/recheck-pipeline.log 2>&1
git diff --check
```
Expected: 16 / 3 / 6 passing tests; whitespace check passes. No AE launch.
For live repetition, with AE absent and screen unlocked, use a fresh scratch path:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py --scratch orchestra/state/A03e-ae-watcher-workspace-and-live/recheck-live --binary orchestra/state/A03e-ae-watcher-workspace-and-live/recheck/ae-dialog-watch > orchestra/state/A03e-ae-watcher-workspace-and-live/recheck-live.log 2>&1
```
Expected: exit 0, two exact scripting=1 markers, exit=0, remaining=[], clicks=0,
false crash flags, and restored=true with equal before/restored hashes.

next:
- Consider a separate ticket to port the proven single post-workspace dispatch
  into run_ae_smoke.py; its -r mechanism was deliberately left unchanged here.
- Live crash-recovery rule acceptance remains unproven; no recovery dialog
  occurred. Do not manufacture one by force-crashing AE or deleting guessed state.
