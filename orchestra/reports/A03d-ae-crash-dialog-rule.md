status: blocked
summary: Implemented fail-closed OCR crash_recovery_layout and screenshot/negative tests.
  Added streamed crash-state inventories and a pre-click snapshot barrier.
  Two live attempts were blocked by watcher surface handling, with no recovery dialog or JSX marker.
  Both owned AE processes exited 0 after normal quit; scripting prefs restored byte-exactly.
  Real crash marker and two unattended successful launches remain unproven.

facts:
- Read AGENT_GUIDE.md, compatibility plan, A03c report and existing watcher code.
  No plugins, release gates, ledger, MAIN or external emulator sources changed.
- `PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py --scratch orchestra/state/A03d-ae-crash-dialog-rule/build`
  passes **12 tests**, including native Vision OCR of A02d and A03c screenshots.
  Both select exactly one layout target; six negative variants per image reject
  missing label, extra box, swapped anchor positions, changed title,
  low-confidence title and overlapping box. Exact-label policy remains intact.
- Busy/lock/memory preflight: no AE, screen unlocked, **44%** free memory.
  Each launch also repeated existing busy/lock/memory checks. Full-path executable
  only; never SIGTERM/SIGKILL, no manual click, no second concurrent AE.
- Live command (exit 1), then same command with `live2` after the confirmed
  vanished-window handling fix (also exit 1):
  ```sh
  PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_e2e.py \
    --scratch orchestra/state/A03d-ae-crash-dialog-rule/live \
    --binary orchestra/state/A03d-ae-crash-dialog-rule/build/ae-dialog-watch \
    > orchestra/state/A03d-ae-crash-dialog-rule/live.log 2>&1
  ```
- First PID **66224**, first failing boundary: splash window **1707** vanished
  during ScreenCaptureKit capture (`Target window unavailable`). No click or
  marker. Normal Apple-event quit requested; exit **0**, remaining processes `[]`.
  Fixed only confirmed window disappearance: skip when the specific window is
  absent and screen capture access still exists; otherwise propagate failure.
- Retry PID **66505**, new boundary: main untitled workspace window **1726**
  (3200×1743 points) failed the existing OCR workspace predicate and emitted
  `Unknown AE dialog; no click`. No marker. Normal quit requested; exit **0**,
  remaining processes `[]`. No third attempt or broader workspace policy change.
- Both attempts have **434 inventory entries before and after**, **4 file hash
  changes** each. Inventories cover all requested roots plus Adobe/Common.
  Changed files: main preferences txt, indep-general txt, domain plist, and
  SCRPriorState.json. The first after-inventory was taken after restoration;
  the second was taken after AE exit and before restoration. These stages are
  explicitly named in the evidence; preference restoration is not an AE change.
  No recovery dialog was observed, so no dialog-state snapshot exists.
- SCRPriorState.json readback was `{"last_match_job":"b1d1c1c3-45ff-18aa-3fe1-49ec00000590"}`.
  Comparing first effective plist backup with subsequent on-disk plist showed
  only SessionDuration changing 8→4; CrashOccurred/ForceQuitOccured remained false.
  This does **not** identify a previous-crash marker. No additional file/key cleared.
- Both scripting-prefs records show restored=true and original/restored SHA-256
  `bb437dbab0b979e92fb55e33051d9331d12f1fc86bb64e33aee8dd16dad77f03`.
  Scripting was not left enabled. Marker runtime acceptance remains unverified.
- Preference tests **3/3**, pipeline tests **6/6**, `git diff --check` passes.
  Logs, inventories, lifecycle and SHA-256 manifest: [A03d-evidence](A03d-evidence/).
  Scratch measured **93 MiB** before removing regenerable build/module cache.
  No background process started by this worker remains. Tools' TMPDIR/TMP/TEMP
  used ticket scratch; an installed third-party AE extension independently logged
  its own `/tmp/nexpression_bridge_66505.sock` path; no worker command wrote there.

inference:
- The layout rule resolves the saved OCR boundary without fuzzy label matching.
  Its live click remains unproven because recovery did not recur.
- A03c's normal quit may have cleared the recovery condition; absent a reproduced
  dialog-state comparison, attributing it to SCRPriorState or another file would
  be speculation. Hash changes alone do not establish crash-state semantics.
- A verified splash disappearance is safe to skip without a click. The retry
  reached a fresh workspace-recognition boundary. Stop here rather than expand
  dialog automation beyond this ticket or claim successful unattended launches.

changed_files:
- tools/ae_smoke/ae_dialog_watch/Policy.swift
- tools/ae_smoke/ae_dialog_watch/main.swift
- tools/ae_smoke/ae_dialog_watch/test_watch.py
- tools/ae_smoke/ae_dialog_watch/test_e2e.py
- tools/ae_smoke/ae_dialog_watch/crash_snapshot.py
- tools/ae_smoke/ae_dialog_watch/README.md
- orchestra/reports/A03d-ae-crash-dialog-rule.md
- orchestra/reports/A03d-evidence/

verify:
```sh
mkdir -p orchestra/state/A03d-ae-crash-dialog-rule/recheck
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_watch.py --scratch orchestra/state/A03d-ae-crash-dialog-rule/recheck > orchestra/state/A03d-ae-crash-dialog-rule/recheck-watch.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/ae_dialog_watch/test_prefs.py orchestra/state/A03d-ae-crash-dialog-rule/recheck > orchestra/state/A03d-ae-crash-dialog-rule/recheck-prefs.log 2>&1
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_pipeline.py > orchestra/state/A03d-ae-crash-dialog-rule/recheck-pipeline.log 2>&1
git diff --check
```
Expected: 12, 3, 6 tests pass; whitespace check passes. No AE launch/pref change.
The live commands above document failures, not an expected passing verification.

next:
- Follow-up: safely recognize the real untitled AE workspace and establish why
  marker JSX was not reached; then repeat two unattended marker/quit launches.
- Retain the snapshot barrier for the next naturally occurring recovery dialog;
  capture before/visible-dialog/clean-quit states and identify the causal marker.
  Do not force-crash AE or delete guessed state to manufacture this evidence.
