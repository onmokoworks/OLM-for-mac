status: blocked
summary: Added reversible scripting prefs with byte-preserving enable, backup/hash/readback and --restore.
  Marker JSX now catches write errors and always calls app.quit() in finally.
  First live launch hit recovery despite both crash flags reading false.
  Native OCR misread 続行 as 綂行 (0.30); allowlist refused, zero clicks, no marker/second launch.
  Normal quit left no AE; original scripting prefs restored byte-exactly. Offline 3+12+6 tests pass.

facts:
- Branch `orch/A03c-ae-scripting-pref-and-live-proof`; read AGENT_GUIDE,
  compatibility plan, A03b/A01 reports and existing watcher/runner. No plugin,
  release gate, ledger, MAIN, emulator or installed bundle changes; no push.
- `git log --all --oneline -S Pref_SCRIPTING_FILE_NETWORK_SECURITY` found only
  ticket assignment commit `84ad9f7b`, not A01 implementation. Installed 26.3
  preference format contains `["Main Pref Section v2"]`, CR newlines and no
  scripting key. New helper targets that section and fails closed on ambiguity.
  Runtime acceptance is explicitly unverified (no marker).
- Preflight via `running()`, `screen_locked()`, `preflight()` returned no AE,
  unlocked and **49%** system memory free. Test repeated busy/lock/memory checks
  before launching. [Preflight](A03c-evidence/preflight.json).
- Exact live command, exit **1**:
  ```sh
  PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py \
    --scratch orchestra/state/A03c-ae-scripting-pref-and-live-proof/e2e \
    --binary orchestra/state/A03c-ae-scripting-pref-and-live-proof/build/ae-dialog-watch \
    > orchestra/state/A03c-ae-scripting-pref-and-live-proof/e2e.log 2>&1
  ```
  One full-path `/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects -r <launch.jsx>` dispatch,
  PID **63206**. No second instance, no SIGTERM/SIGKILL, no manual click.
- Watcher started before preference changes and launch, AXObserverCreate=0.
  Prevention backed up effective/on-disk plists; both CrashOccurred and
  ForceQuitOccured read **0 before and after** writing false.
  [Full paths/hashes/readbacks](A03c-evidence/prevention.json).
- Scripting helper copied original txt and recorded SHA-256
  `bb437dbab0b979e92fb55e33051d9331d12f1fc86bb64e33aee8dd16dad77f03`.
  It inserted the absent key as `01`, read it back, resulting hash
  `430246f0c124df2ba0e2128c41c2618ecdeee20db8cc644ecea120215ace4fde`.
  After AE disappeared, full original file was restored; restored hash equals
  the original above. Preference was **not left enabled for A02e**.
  [Preference record](A03c-evidence/scripting-prefs.json). Private backups remain
  in scratch, not committed; they are no longer needed to undo this completed restore.
- First failing boundary: recovery dialog window **1670**, **525×373 points**,
  scale **2**, **1050×746 native pixels**. Vision read heading correctly but
  button `綂行`, confidence **0.30**, not exact allowlisted `続行`.
  Watcher emitted `no-safe-button` then `blocked`; **0 click events**.
  [Native image](A03c-evidence/no-safe-button-1670.png),
  [OCR/events](A03c-evidence/dialogs.jsonl).
  Image SHA-256 `b519cf65a038723059dd1d500c69ddc3487b20628a0f32f9369d904b1b19f10a`.
  Visual inspection confirms the displayed label is 続行. No fuzzy alias,
  coordinate fallback, threshold change or allowlist change was made.
- Failure handler inspected owned windows 1676/1677, then capture timed out
  ([inspection](A03c-evidence/blocked-capture.jsonl)). It sent one normal
  Apple-event quit; quit log empty, no timeout text. Final process list `[]`.
  Marker absent; second-launch directory absent. Flags remain **0/0**.
  [Final state](A03c-evidence/final-state.json). The AE executable exit status
  was not persisted on this failure path, so a clean exit-code-0 claim is not made.
  Final code now saves lifecycle exit/quit-request state for future attempts.
- Watcher stopped on its safety failure; it did not monitor the remainder of
  cleanup. Thus continuous successful monitoring through clean exit is **not** proven.
  No background process started by this worker remains.
- Offline preference tests **3/3**, watcher/policy/native fixture tests **12/12**,
  pipeline tests **6/6**; `git diff --check` passes. Logs and evidence hashes in
  [evidence directory](A03c-evidence/sha256.json). Final cleanup structure was
  reviewed/syntax-checked; no second live dispatch was made after the blocker.
- Scratch peaked at measured **89 MiB**, below 5 GiB; regenerable Swift binary
  and module cache removed, build log retained. TMPDIR/TMP/TEMP during live run
  pointed into ticket scratch. No worker scratch was created in `/tmp`.

inference:
- Observed false flags were insufficient to prevent recovery in this launch;
  the reason is unresolved. Do not infer that enabling scripting caused recovery.
- Native scale alone did not solve this label recognition. The watcher correctly
  refused an unrecognized low-confidence label. This is a fresh native OCR boundary,
  not proof of a scripting-file failure or successful runtime preference handling.
- Stop at the allowlist blocker; do not launch repeatedly or claim two clean runs.

changed_files:
- `tools/ae_smoke/ae_dialog_watch/prefs.py`
- `tools/ae_smoke/ae_dialog_watch/test_prefs.py`
- `tools/ae_smoke/ae_dialog_watch/test_e2e.py`
- `tools/ae_smoke/run_ae_smoke.py`
- `tools/ae_smoke/ae_dialog_watch/README.md`
- `tools/ae_smoke/README.md`
- `orchestra/reports/A03c-ae-scripting-pref-and-live-proof.md`
- `orchestra/reports/A03c-evidence/`

verify:
```sh
mkdir -p orchestra/state/A03c-ae-scripting-pref-and-live-proof/recheck
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_prefs.py \
  orchestra/state/A03c-ae-scripting-pref-and-live-proof/recheck \
  > orchestra/state/A03c-ae-scripting-pref-and-live-proof/recheck-prefs.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py \
  --scratch orchestra/state/A03c-ae-scripting-pref-and-live-proof/recheck \
  > orchestra/state/A03c-ae-scripting-pref-and-live-proof/recheck-watch.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py \
  > orchestra/state/A03c-ae-scripting-pref-and-live-proof/recheck-pipeline.log 2>&1
git diff --check
```
Expected: 3, 12 and 6 tests pass, whitespace check passes. No AE launch or real
preference change. Live command above describes a measured failure, not an
expected successful test; use fresh scratch only after resolving this blocker.
Manual prefs enable/restore syntax is documented in the watcher README.

next:
- Investigate the recovery source despite 0/0 flags and exact native 続行 OCR
  using retained image; preserve the exact-label and confidence policy.
- Then run two full-path marker launches with watcher throughout, exit-code 0,
  no remaining process and flags false; verify runtime scripting=1 and restore.
- A02e should not assume unattended launch success from this ticket.
