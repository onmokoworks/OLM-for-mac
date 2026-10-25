status: partial
summary: Screen locked at preflight; no AE launch or render attempted.
  Waiting at five-minute intervals, up to the specified 12 hours.
  Added fail-closed GUI lock guard and ticket-local scratch override.
  Added optional 16/32 bpc untouched-default matrix; not validated in AE.
  Corpus and oracle comparison remain outstanding.

facts:
- Initial `ioreg -n Root -d1 -a | plutil -extract IOConsoleUsers.0.CGSSessionScreenIsLocked raw - 2>/dev/null`: true. No main AE process; memory free 60%.
- Branch `orch/A02b-real-ae-retest-downsample`, initially clean. No installed bundle/plugin source/release gate/ledger/MAIN changes; no build or push.
- Ten installed executable hashes retained in `A02b-evidence/installed.json` (not loaded-module proof).
- `run_ae_smoke.wait_unlocked` is polling without launching AE. First Python probe exposed dictionary-shaped ioreg plist; parser corrected to accept dictionary or array roots and reject unknown lock evidence.
- Pipeline tests 4/4, comparison tests 4/4, render-result tests 2/2 passed. After adding depth support, render test fixtures needed explicit depth; 2/2 pass again. Initial existing render tests used their historical A02 scratch directory and removed temporary files; subsequent tests use this ticket's scratch.
- Input generation plus `decode.decode` hash check: 7/7 file roundtrips exact (three 8-bit sizes, two sizes each at 16/32 bpc); hashes in `A02b-evidence/input-validation.log`. This is NOT AE I/O calibration.
- AE launches 0; rendered frames 0; AE/original/native-host comparisons 0. First mismatch and timing unavailable.

inference:
- The locked desktop blocks the required GUI JSX build. No plugin behavior can be inferred from it.
- Checked-in A01c report records no completed I/O calibration; the ticket premise of calibration is not used as measured evidence.

changed_files:
- tools/ae_smoke/run_ae_smoke.py
- tools/ae_smoke/downsample_inputs.py
- tools/ae_smoke/prepare_downsample.jsx
- tools/ae_smoke/render_downsample.py
- tools/ae_smoke/test_pipeline.py
- tools/ae_smoke/test_downsample.py
- tools/ae_smoke/README.md
- orchestra/reports/A02b-real-ae-retest-downsample.md
- orchestra/reports/A02b-evidence/

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02b-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02b-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_downsample.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
git diff --check
```
Expected: 4 + 2 + 4 offline tests pass, whitespace check passes. Recreate the venv with numpy/tifffile/OpenEXR in ticket scratch if absent. No AE outcome is promised.

next:
- Continue waiting for unlock; then priority build/render and exact controls, followed by depth defaults, corpus and original/same-bundle comparisons.
- Preserve untouched DistanceGradation 32 bpc defaults; no plugin fix is justified before a measured failure.

checkpoint: 2026-10-25T02:45:14.048638+00:00; 7 lock polls recorded; AE not launched. See A02b-evidence/screen-lock.txt.

checkpoint: 2026-10-25T03:14:38.764312+00:00; 13 lock polls recorded; AE not launched.

checkpoint: 2026-10-25T03:43:57.244525+00:00; 19 lock polls recorded; AE not launched.

checkpoint: 2026-10-25T04:13:06.467494+00:00; 25 lock polls recorded; AE not launched.

checkpoint: 2026-10-25T04:42:15.843300+00:00; 30 lock polls recorded; AE not launched.
