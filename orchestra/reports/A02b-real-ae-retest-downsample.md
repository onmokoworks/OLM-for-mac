status: blocked
summary: No AE launch: screen stayed locked, then macOS stopped exposing its lock state.
  Resumed the original wait; stopped safely on unknown state before the 12-hour deadline.
  Added restart-safe lock deadline and optional 16/32 bpc untouched-default scaffold.
  Offline tests pass; no AE render, timing, refusal or exactness result exists.
  Corpus mapping and original/same-bundle comparison remain outstanding.

facts:
- Branch `orch/A02b-real-ae-retest-downsample`. Resumed existing work/checkpoints rather than restarting the ticket. No installed bundle, plugin source, MAIN, emulator source, release gate or ledger changes; no build, push, stash or history rewrite.
- Lock evidence: **88** successful probes, all `locked=True`, from **2026-10-25 02:12:57.363 UTC** through **09:48:14.979 UTC**. There was an orchestrator-restart gap; this is not a claim of continuous observation. [Log](A02b-evidence/screen-lock.txt).
- Resumed `run_ae_smoke.wait_unlocked(Path('orchestra/state/A02b-real-ae-retest-downsample'))` with `PYTHONDONTWRITEBYTECODE=1 python3 -u`; exit **1** at the next scheduled poll: `RuntimeError: Cannot establish screen lock state; launch refused`. [Log](A02b-evidence/resumed-lock-wait.log). Original deadline was **14:12:57.363 UTC**, not reached. The helper now preserves that deadline across restarts.
- At **09:53:19 UTC**, the prescribed `ioreg -n Root -d1 -a | plutil -extract IOConsoleUsers.0.CGSSessionScreenIsLocked raw - 2>/dev/null` could not extract the key. Follow-up plist inspection at **09:53:43 UTC** found one IOConsoleUsers entry with no `CGSSessionScreenIsLocked` key. [Sanitized preflight](A02b-evidence/final-preflight.json). Unknown is not treated as unlocked.
- `pgrep -fl 'MacOS/After Effects$'`: no matches at resumed and final preflight. Resumed `memory_pressure`: **42%** free (initial pre-restart record: 60%). No AE/aerender or emulator process was started; both read-only osascript probes and the lock waiter exited.
- Read-only System Events queries for application-process paths and `UI elements enabled` both returned Apple-event timeout **-1712**. [Inventory query error](A02b-evidence/accessibility-preflight.log), [UI-access query error](A02b-evidence/accessibility-enabled.log). No -1719/-25211 denial was observed, so Accessibility permission status is unverified. No dialogs inspected/clicked, no screenshot, no `dialogs.jsonl` click entries, no quit or force-shutdown action.
- Ten installed executable hashes retained in [installed.json](A02b-evidence/installed.json); these are not loaded-module proof. Seven generated input file roundtrips exact (three 8-bit sizes, two sizes each at 16/32 bpc): [hash evidence](A02b-evidence/input-validation.log). These are not AE I/O calibration.
- Final offline tests: pipeline **5/5**, render attribution **2/2**, comparator **4/4** pass; `git diff --check` passes. Logs: [pipeline](A02b-evidence/final-pipeline-tests.log), [render](A02b-evidence/final-downsample-tests.log), [compare](A02b-evidence/final-compare-tests.log).
- AE launches **0**, effect/control frames **0**, original/native-host comparisons **0**. First mismatch, refusal tags, actual AE downsample/InData values and timings are unavailable. No black plugin frame or plugin bug was established.
- Priority scaffold: 120 effect frames + 12 controls (10 defaults × 3 sizes × 4 resolutions), 8 bpc. Optional depth scaffold: 160 effects + 16 controls (10 defaults × 2 sizes × 4 resolutions × 16/32 bpc), including untouched DistanceGradation 32 bpc. Both remain unvalidated in AE; corpus cases are not implemented.

NT = not tested. The 8 bpc columns cover 1920×1080, 1279×719 and 3840×2160; 16/32 bpc cover the first two sizes. No cell is OK/black/render-error/exact-vs-original.

| Plugin | Full 8 | Half 8 | Third 8 | Quarter 8 | All resolutions 16 | All resolutions 32 |
| --- | --- | --- | --- | --- | --- | --- |
| OLMBlur | NT | NT | NT | NT | NT | NT |
| ColorKeep | NT | NT | NT | NT | NT | NT |
| OLMColorKey | NT | NT | NT | NT | NT | NT |
| OLMDirectionalBlur | NT | NT | NT | NT | NT | NT |
| OLMDistanceGradation | NT | NT | NT | NT | NT | NT |
| OLMKiraKira | NT | NT | NT | NT | NT | NT |
| OLMSmoother2 | NT | NT | NT | NT | NT | NT |
| OLMToonDilate | NT | NT | NT | NT | NT | NT |
| OLMRadialBlur | NT | NT | NT | NT | NT | NT |
| OLMSmoother | NT | NT | NT | NT | NT | NT |

| Timing scope | 1080p seconds/frame | 4K seconds/frame |
| --- | --- | --- |
| All ten plugins, Full/Half/Third/Quarter, 8 bpc defaults | unavailable (0 frames) | unavailable (0 frames) |

inference:
- The desktop/session precondition blocks the GUI build. The missing key may reflect a console-session transition, but its cause is not established; neither unlock nor logout is asserted.
- System Events timeouts do not prove an Accessibility denial or identify a particular dialog. No permission claim or dialog dismissal is inferred.
- The checked-in A01c report records no completed AE I/O calibration, contrary to the ticket premise. Calibration must be measured before interpreting effect differences.
- No I/O/color-management/host-geometry/plugin-bug classification is possible with zero frames. No plugin fix ticket is justified.

changed_files:
- tools/ae_smoke/run_ae_smoke.py: fail-closed lock guard, scratch override, optional depth matrix, restart-safe 12-hour deadline.
- tools/ae_smoke/downsample_inputs.py, prepare_downsample.jsx, render_downsample.py: optional 16/32 bpc default inputs/projects/output decoding.
- tools/ae_smoke/test_pipeline.py, test_downsample.py, README.md.
- orchestra/reports/A02b-real-ae-retest-downsample.md, A02-real-ae-retest-downsample.md, A02b-evidence/.

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02b-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02b-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_downsample.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
git diff --check
# Read-only console/process checks; do not launch on missing/true lock state:
ioreg -n Root -d1 -a | plutil -extract IOConsoleUsers.0.CGSSessionScreenIsLocked raw - 2>/dev/null
pgrep -fl 'MacOS/After Effects$'
```
Expected offline: **5 + 2 + 4** tests pass and whitespace check passes. Recreate the venv with numpy/tifffile/OpenEXR in ticket scratch if absent. The live lock/process state may change; the recorded final result was missing key/no main-process match. No successful AE outcome is promised.

next:
- Restore a verifiably unlocked console session and verify System Events access. Resume priority build/render with a fresh preflight and the existing unused priority run directory; retain full-path single dispatch, 180-second timeout, no force quit and authorized dialog limits.
- Validate AE I/O controls and actual queue/downsample/InData geometry, then F53 original and same-installed-bundle comparisons. Preserve untouched DistanceGradation 32 bpc defaults.
- Implement two corpus parameter cases per plugin only with verified AE property mapping/readback. Complete the requested matrix and report timings. Create black-frame/plugin-fix tickets only from measured minimal repros.

cleanup:
- Scratch **279 MiB**, below 5 GiB. No generated build trees or background process started in this resume remains. Logs and small evidence are committed; generated inputs/local venv retained for a later authorized resume. Installed bundles unchanged.
