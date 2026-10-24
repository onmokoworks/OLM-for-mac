status: blocked
summary: Fresh HEAD Universal/minos-11.0 bundles built and installed in both allowed folders.
  AE 2026 26.3x87 registered/applied all 10; vmmap binds all 10 to OLM-smoke.
  Parameter dumps retained; full source/param comparison and render matrix remain incomplete.
  AE 2025 sign-in modal blocked its probe; AE 2026 relaunch showed sign-in but its probe completed.
  Rosetta unavailable in installed AE 2026 (arm64-only executable).

facts:
- Source HEAD: `f07c000a0a69acce6daa0380b254a0699d7e69a4`, branch `orch/A01-real-ae-smoke`; initial worktree clean.
- Both `/Applications/Adobe After Effects {2026,2025}/Plug-ins/OLM-smoke/` existed and were writable. No sudo and no writes elsewhere under /Applications or /Library.
- Initial `pgrep -fl 'After Effects'`: no matching processes. `memory_pressure`: 84% system-wide memory free. Per-launch memory samples retained.
- `python3 tools/fuzz/build_F47_bundles.py --scratch /Users/onmk/.cache/olm-emu/A01`: exit 0, 10/10 built, one Xcode job. `lipo -info` and `xcrun vtool -show-build`: arm64+x86_64 and minos 11.0 for both slices of all 10.
- [Bundle hashes/build identity/install paths](A01-evidence/bundles.json) retain SHA-256 for every executable. Installed copies rechecked: 20/20 SHA-256 matches.
- Direct AE 2026 `After Effects -r <launch-2026.jsx>` followed by bounded `osascript ... DoScriptFile POSIX file <launch-2026.jsx>`: probe completed; both dispatch mechanisms were used, so the initial completion is not attributed uniquely to one. `get version` returned `26.3.0`; JSX `app.version` returned `26.3x87`.
- [Raw first probe](A01-evidence/probe-2026.json): 465 registered effects, 10/10 expected PiPL match names registered, 10/10 applied. [vmmap excerpt](A01-evidence/vmmap-2026-plugins.txt): all 10 OLM-smoke executable paths mapped. No old MediaCore OLM executable mapping appears. Existing user MediaCore OLM bundles were observed during preflight; this worker did not move/change them.
- Raw property dumps include AE's built-in compositing group; counts below are top-level children, **not** PF parameter counts. Third-party popup label readback is not implemented and is explicitly null.
- Static check of `mac/OLMBlur/OLMBlur.cpp:69`: default/bounds agree for Blur Amount 5 [1,1000], Smoothness 100 [1,100], Repeat 2 [1,10], Bias 1 [1,2], Legacy false. `mac/OLMToonDilate/OLMToonDilate.cpp:83`: Search Radius 2 [0,100] agrees. This does not complete type/label/source comparison.
- AE 2025 `-r` plus `DoScriptFile` did not produce valid probe JSON (zero-byte output). An Adobe sign-in/password modal was captured. No modal was clicked and no credentials were entered by this worker.
- A subsequent AE 2026 probe displayed a sign-in modal, but completed 10/10 rows and output template enumeration through `DoScriptFile`; [template evidence](A01-evidence/templates-2026.json) retained. The modal alone is not evidence that scripting always fails.
- `lipo -info '/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects'`: only arm64. No x86_64 launch/render attempted.
- The default-project preparation driver encountered a **new non-owned AE 2025 session** (PID 10779); it waited and repeated the busy check at five minutes. No default-project JSX was launched. With the captured sign-in blocker and incomplete 2025 probe, the pending driver was stopped and this blocked report finalized; the two-hour busy timeout was **not** reached. The non-owned AE session was left untouched.
- `prepare_inputs.py`: existing OLMBlur adapter seed 1 generated SDR inputs: 8 bpc index 0, 21x19; 16 bpc index 3, 20x23; 32 bpc index 2, 10x19. 16-bit TIFF and uncompressed FLOAT EXR written, with unmodified source ARGB retained in scratch. [Input hashes](A01-evidence/inputs.json). No I/O-faithfulness claim yet.
- `python3 tools/ae_smoke/test_compare.py`: 4 tests pass (all depths equal, first mismatch x/y/ARGB, signed-zero/NaN payload differences, wrong length). Synthetic tests are not plugin results.

| Plugin | AE 2026 registered / applied | Dump children | Params OK? | 8 bpc render | 16 bpc render | 32 bpc render |
|---|---|---:|---|---|---|---|
| OLMBlur | yes / yes | 6 | Values/bounds checked; labels/type mapping incomplete | not run | not run | not run |
| ColorKeep | yes / yes | 102 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMColorKey | yes / yes | 224 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMDirectionalBlur | yes / yes | 22 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMDistanceGradation | yes / yes | 13 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMKiraKira | yes / yes | 41 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMSmoother2 | yes / yes | 16 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMToonDilate | yes / yes | 2 | Radius value/bounds checked; type mapping incomplete | not run | not run | not run |
| OLMRadialBlur | yes / yes | 31 | Dumped; source comparison incomplete | not run | not run | not run |
| OLMSmoother | yes / yes | 4 | Dumped; source comparison incomplete | not run | not run | not run |

AE vs host: **not run for any plugin**. Exact/diff classification, mismatching sample counts, and first mismatch are unavailable. No aerender output, Smart callback trace, no-effect I/O round trip, or host output exists; nothing is classified as a plugin bug.

AE 2025: all 10 load/params/render cells **unverified**, due to incomplete probe with sign-in modal. Rosetta: **unsupported by the installed AE 2026 executable**, not a bundle architecture failure.

Screenshots:
- `orchestra/reports/A01-evidence/screens/blocked-2025.png`: AE 2025 sign-in/password modal.
- `orchestra/reports/A01-evidence/screens/relaunch-2026.png`: AE 2026 sign-in modal on relaunch; subsequent script completion is recorded separately.
- No per-plugin Effect Controls screenshots were obtained. These two captures are blocker evidence, not UI conformance evidence.

inference:
- The initial real-host load/application boundary is established for these hashes; neither rendering nor bit-exact output follows from that.
- The AE 2025 modal is a plausible cause of its incomplete script output; a causal diagnosis was not established. User sign-in/first-launch completion is the suggested prerequisite before a new 2025 probe.
- The 2026 executable has no x86_64 slice, so Rosetta cannot exercise this installed version.

changed_files:
- `tools/ae_smoke/run_ae_smoke.py`: guarded build/install/probe driver, bounded scripting fallback, parameter/template or render-project preparation stage; does not implement the full matrix.
- `tools/ae_smoke/probe.jsx`: PiPL-driven registration, property dump, template enumeration.
- `tools/ae_smoke/prepare_inputs.py`, `prepare.jsx`: deterministic input generation and **unvalidated** default-project preparation.
- `tools/ae_smoke/compare.py`, `test_compare.py`, `verify_evidence.py`, `README.md`.
- `orchestra/reports/A01-real-ae-smoke.md` and `orchestra/reports/A01-evidence/`.
- Outside git, authorized bundle installs below and cache entry `A01-bundles-f07c000a0a69acce` in `~/.cache/olm-emu/INDEX.json`; cache build manifest `~/.cache/olm-emu/A01/build.json`. No plugin sources, release gates, forbidden-action lists, MAIN files, or emulator source changed.

verify:
```sh
python3 tools/ae_smoke/verify_evidence.py
python3 tools/ae_smoke/test_compare.py
python3 -m py_compile tools/ae_smoke/*.py
```
Expected: 10/10 retained load/apply/mapping records, 20/20 currently installed hashes; 4 comparator tests pass; Python syntax succeeds. This does not launch AE and does not validate rendering.

After user sign-in and after all AE instances are closed, use a new run ID:
```sh
python3 tools/ae_smoke/run_ae_smoke.py --run-id retry2026 --year 2026
python3 tools/ae_smoke/run_ae_smoke.py --run-id retry2025 --year 2025
```
Expected if AE is scriptable: `phase=complete`, 10 registered/applied rows under `orchestra/state/A01-real-ae-smoke/<run-id>/probe-<year>.json`. If a modal blocks scripting: bounded timeout, screenshot, failure. This expected result is conditional, not a measured 2025 success. See `tools/ae_smoke/README.md` for the unvalidated preparation stage and remaining limitations.

Installed bundles intentionally left for the user:
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMBlur.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMBlur.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/ColorKeep.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/ColorKeep.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMColorKey.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMColorKey.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMDirectionalBlur.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMDirectionalBlur.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMDistanceGradation.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMDistanceGradation.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMKiraKira.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMKiraKira.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMSmoother2.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMSmoother2.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMToonDilate.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMToonDilate.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMRadialBlur.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMRadialBlur.plugin`
- `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/OLMSmoother.plugin`
- `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/OLMSmoother.plugin`

cleanup:
- Owned AE application PIDs 7512 (first 2026), 7977 (2025), and 9449 (second 2026) exited. Their observed installation-local helper processes were terminated; pending driver PID 11156 was terminated before it launched an AE. No non-owned AE was signaled.
- No preferences were changed, so no preference restoration was needed. No instrumented bundles were installed.
- Regenerable venv and Python cache files removed. The builder removed obj/pch trees; final cache products intentionally remain at `~/.cache/olm-emu/A01/xcode/<plugin>/products/<plugin>.plugin`, registered in the cache index.

next:
- Resume A01 after the user's AE session ends and Adobe sign-in is resolved; complete source/default/type/popup comparison.
- Validate the prepared default projects and output template settings; run aerender 30 default cells plus 90 exact-corpus cells, with no-effect controls and verified Smart dispatch.
- Implement/verify F47 native-worker pixel and parameter mapping, TIFF/EXR conversion and exact I/O gates before classifying differences. Do not bake host conversion into plugin code.
- Run AE 2025 default cells and obtain ten Effect Controls screenshots by script. Rosetta needs an AE installation with an x86_64 executable.
