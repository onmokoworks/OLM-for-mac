status: blocked
summary: One AE 2026 launch produced no JSX marker within 180 seconds.
  Captured a black screenshot crop and attempted normal quit once; no retry or signals.
  Added an opt-in priority matrix and per-frame aerender logging, not real-host validated.
  No frames, numerical comparisons or timing measurements obtained.
  Higher depths, corpus cases and oracle/native-host comparison remain unimplemented.

facts:
- Branch `orch/A02-real-ae-retest-downsample`, initial HEAD `b924f09a`, initially clean. MAIN, plugin sources, installed bundles, emulator sources, release gates and ledger unchanged. No builds, push, stash or history rewrite.
- Checked-in A01c report/README record startup timeout and uncalibrated I/O, contrary to ticket premise of completed exact I/O. No previous calibration was assumed.
- Initial exact-main process check found no AE/aerender. Initial memory free 63%; launch preflight retained in [memory.txt](A02-evidence/memory.txt).
- Created ticket-local venv with numpy/tifffile/OpenEXR. Three opaque 8-bit TIFF/ARGB patterns at 1920×1080, 1279×719, 3840×2160 have RGB 32..223 and alpha 255. [Input hashes](A02-evidence/inputs.json). [Ten installed executable hashes](A02-evidence/installed.json) do not establish loaded-module identity.
- Ran `PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-priority --stage build --run-id priority`, redirected to scratch; exit **1**. [Build log](A02-evidence/build-run.log).
- One dispatch to `/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects -r <absolute launch.jsx>`; PID **13667**, 2026-10-25 11:05 JST. `OLM_REFUSAL_TRACE` set to scratch. At 180 seconds: no entry/done marker, AEP, frame or refusal file. [Launch wrapper](A02-evidence/launch.jsx), [AE log](A02-evidence/ae.log).
- Timeout capture is a **17,060-byte black screenshot crop**, not a black plugin frame: [image](A02-evidence/blocked.png). One full-app-path osascript quit timed out at 20 seconds: [quit log](A02-evidence/quit.log). No SIGTERM/SIGKILL, fallback dispatch, dialog interaction or second launch. Subsequent `ps -axo pid=,comm=` check found no executable ending `MacOS/After Effects` or `/aerender`. The quit timeout alone does not prove successful quit.
- Priority scaffold requests **120 effect frames + 12 controls**: ten untouched defaults × three sizes × Full/Half/Third/Quarter. JSX reads parameter and render-queue settings. It never executed successfully; queue setting acceptance and actual InData/downsample remain unverified.
- Rendered effects **0/120**, controls **0/12**; original and native-host comparisons **0**. Mismatch counts/first mismatch unavailable, not zero. No I/O/color-management/host-geometry/plugin-bug classification possible.
- Offline tests: pipeline **3/3**, byte comparator **4/4**, new render-result attribution **2/2** passed. New tests reject green status on nonzero process exit despite an output, and flag zero-alpha/nonzero-RGB output. Python compilation and whitespace checks passed. These are not real-host proof.
- Automatic approval review rejected a combined report/cleanup/commit command because `rm -rf` was disallowed; that entire command did not execute. Reissued report and commit separately with narrowly scoped cleanup.

NT = not tested due to startup failure. Each planned 8 bpc cell covers all three sizes. Higher-depth generation remains unimplemented. No cell is OK, black, render-error or exact-vs-original.

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
| All ten plugins, all four resolutions, 8 bpc defaults | unavailable (0 frames) | unavailable (0 frames) |

inference:
- Failure precedes JSX entry evidence. The black screenshot cannot distinguish startup modal, window visibility, display capture or another startup failure; a crash-recovery dialog is not established.
- No evidence supports a plugin fix or confirms real-AE downsample behavior. The mandatory startup-timeout stop ended work, not two refuted numerical hypotheses.

changed_files:
- `tools/ae_smoke/run_ae_smoke.py`: opt-in priority matrix/scratch; refusal environment; five-minute busy polling and aerender guard; reject unimplemented priority compare/all. Legacy remains default.
- `tools/ae_smoke/downsample_inputs.py`: deterministic opaque/nonblack input generator.
- `tools/ae_smoke/prepare_downsample.jsx`: separate default matrix, queue settings/property readbacks, normal quit.
- `tools/ae_smoke/render_downsample.py`: serial one-item aerender, per-frame exit/output/trace, black/transparent flags, dimensions/hash and wall timing including startup.
- `tools/ae_smoke/test_downsample.py`, `tools/ae_smoke/README.md`.
- This report and `orchestra/reports/A02-evidence/`.

verify:
```sh
# Offline; no AE launch:
python3 -m venv orchestra/state/A02-real-ae-retest-downsample/venv
TMPDIR="$PWD/orchestra/state/A02-real-ae-retest-downsample" orchestra/state/A02-real-ae-retest-downsample/venv/bin/pip install numpy tifffile OpenEXR
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 orchestra/state/A02-real-ae-retest-downsample/venv/bin/python tools/ae_smoke/test_downsample.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
PYTHONPYCACHEPREFIX="$PWD/orchestra/state/A02-real-ae-retest-downsample/pycache" python3 -m py_compile tools/ae_smoke/*.py
git diff --check
```
Expected: 3 + 2 + 4 tests pass, syntax/whitespace checks pass. The build command in facts is the exact attempted invocation, not a promised successful run. Do not blindly retry before startup is independently resolved; a fresh run-id is required. JSX/render stage remain unvalidated in AE.

next:
- **A02a-startup**: independently diagnose missing JSX marker from exact AE 2026 dispatch, respecting busy/single-launch/no-force-quit rules. Screenshot establishes no dialog cause.
- **A02b-priority-render**: validate queue settings, render priority frames, calibrate I/O, capture actual downsample/InData and odd-size output geometry, run F53 original and same-installed-bundle fallback comparisons.
- **A02c-depth-corpus**: add 16/32 bpc and two exact corpus cases per plugin with verified parameter mapping/provenance; retain untouched DistanceGradation 32 bpc defaults.
- No plugin bug/black-frame fix ticket justified with zero rendered frames. Create those from minimal measured repros only.

cleanup:
- Scratch approximately 142 MiB before removing regenerable local venv/pycache, below 5 GiB. Logs and inputs retained; evidence committed. No emulator/build worker started. Final AE/aerender inventory empty.
