status: blocked
summary: One full-path AE 2026 launch timed out at 180 seconds with a crash-recovery dialog.
  No JSX marker, project, render or numerical AE comparison was produced; no retry was attempted.
  Removed fallback dispatch and forced termination; added staged default-project/aerender/control scaffolding.
  Fresh original-AEX PARAMS_SETUP traces confirm all eight audited popup registrations match port source.
  Full 120-cell matrix, calibrated I/O and same-bundle host comparison remain incomplete.

facts:
- Branch `orch/A01c-real-ae-render-aerender`; initial working tree clean. MAIN, emulator source, installed bundles, plugin sources, ledger and release gates were not modified. No builds or installs, no push or history rewrite.
- Initial exact-main process check found no AE. Launch preflight `memory_pressure` is retained in [memory.txt](A01c-evidence/memory.txt).
- Created a ticket-local venv with numpy/tifffile/OpenEXR. `prepare_inputs.py` completed with the existing deterministic seed-1 adapter inputs; [input hashes](A01c-evidence/inputs.json). These inputs have **not** passed an AE round trip.
- Ran `orchestra/state/A01c-real-ae-render-aerender/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --stage build --run-id defaults`, redirected to scratch. Driver exited **1**. [Log](A01c-evidence/build-run.log).
- Started owned PID **25857** using `/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app/Contents/MacOS/After Effects -r <absolute launch.jsx>`. Exactly one script dispatch. No name/bundle-id dispatch, no 2025 launch, no DoScriptFile fallback.
- At **180 seconds**, no `build.json` entry/done marker existed and no AEP existed. Captured [crash recovery dialog](A01c-evidence/blocked-2026.png), then sent one `tell application "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app" to quit` Apple event. It returned **-1708**, “quitを続けることができません。” [Quit log](A01c-evidence/quit.log). PID 25857 was absent at subsequent inspection, and final `ps -axo pid=,comm=` found no executable ending `MacOS/After Effects`. No SIGTERM/SIGKILL or helper signals were sent. No dialog was clicked. No retry was made.
- `popup_audit.py --scratch orchestra/state/A01c-real-ae-render-aerender/popups` completed: **8/8** popup registrations faithful, across three original AEX binaries. It ran cached F46 sessions serially, with a 1×1 dummy input and no render commands; read `session_ready.setup.parameters`, checked setup errors were zero. No worker rebuilt. Raw length-prefixed session transcripts and the full [hash-bound comparison](A01c-evidence/popup-audit.json) are committed.
- Original worker SHA-256: `6616943ba74e07d7f1c0209fe8e650bd496f6caa92fc5a1d3a4151063a36a903`. AEX SHA-256 values and exact commands are in the popup comparison. Labels, registered count and registered default match A01b's captured source declarations. This is fresh original registration tracing, not a new PiPL disassembly or Windows AE UI test.
- The table below combines **fresh AEX trace** and **historical A01 AE 26.3x87 readback**, explicitly identified in each JSON row. Today's JSX did not execute, so today's AE properties/choice counts are unavailable. Historical AE max values follow the number of labels, not the registered count, for these four count mismatches.

| Popup | Original / port count | Label count | Original / port default | Historical A01 AE value; min–max | Registration classification |
| --- | --- | --- | --- | --- | --- |
| DirectionalBlur Noise Type | 2 | 3 | 1 | 1; 1–3 | faithful |
| DistanceGradation In/Out | 3 | 3 | 0 | 1; 1–3 | faithful |
| DistanceGradation Blur Mode | 5 | 3 | 1 | 1; 1–3 | faithful |
| KiraKira Channel | 6 | 4 | 1 | 1; 1–4 | faithful |
| KiraKira Blur Mode | 3 | 4 | 2 | 2; 1–4 | faithful |

- Additional popup registrations DistanceGradation Render Mode / Interpolation Mode and KiraKira Merge mode also match (8 total). No popup source change was made.
- `test_pipeline.py`: **3 tests passed**, including all **32,769** SDR uint16 values through the mathematical TIFF scaling inverse and main-executable detection excluding helpers. `test_compare.py`: **4 tests passed**. `python3 -m py_compile tools/ae_smoke/*.py`: exit 0 with scratch pycache. `git diff --check`: passed. These are offline checks, not AE pixel proof.
- Rendered I/O controls: **0/3**. Rendered default effects: **0/30**. Rendered corpus cells: **0/90**. AE-vs-host comparisons: **0**. Sample mismatch counts and first mismatch: **unavailable**, not zero. No numerical difference is classified as a plugin bug, color issue or host/InData issue. No corpus case was skipped as intrinsically unreproducible; the common startup boundary blocked them all.

inference:
- The captured crash-recovery dialog plausibly prevented the single `-r` JSX from starting. Its reappearance after the reported user recovery is observed; its cause and persistence mechanism are not established. The -1708 quit error does not establish a successful quit, even though the process was subsequently absent.
- The five suspicious popup declarations are faithful to original AEX registration. The historical AE ranges/default clamp suggest host normalization of inconsistent declarations; this is not a current native-Windows UI comparison and does not establish normal UI reachability in Windows.
- The single-GUI-build design is not yet validated. Current code prepares only defaults plus controls, saves three projects because bpc is project-wide, then quits; the corpus/native-host phases still require implementation after startup is resolved.

changed_files:
- `tools/ae_smoke/run_ae_smoke.py`: 2026-only full-path single dispatch, exact executable busy check using `comm`, memory gate, 180-second deadline, screenshot + one normal quit, staged build/render/control-compare commands. Removed old bundle installation and unsafe signal/fallback paths.
- `tools/ae_smoke/prepare.jsx`: property readback and close/quit after building all depth projects. Never reached in this attempt.
- `tools/ae_smoke/decode.py`: strict TIFF/FLOAT EXR ARGB decoding and control checks; **uncalibrated in AE**.
- `tools/ae_smoke/popup_audit.py`: reproducible original parameter registration trace and source/historical-AE comparison.
- `tools/ae_smoke/test_pipeline.py`, `tools/ae_smoke/README.md`.
- This report and `orchestra/reports/A01c-evidence/`.

verify:
```sh
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/test_compare.py
# Requires numpy (or recreate the README venv after cleanup):
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/ae_smoke/test_pipeline.py
PYTHONDONTWRITEBYTECODE=1 python3 tools/ae_smoke/popup_audit.py --scratch orchestra/state/A01c-real-ae-render-aerender/popup-recheck
PYTHONPYCACHEPREFIX="$PWD/orchestra/state/A01c-real-ae-render-aerender/recheck-pycache" python3 -m py_compile tools/ae_smoke/*.py
git diff --check
```
Expected: 4 + 3 offline tests pass; 8 popups / 8 faithful registrations with the recorded AEX/worker hashes; syntax and whitespace checks pass. Popup JSON command paths differ with scratch directory. These commands do not launch AE or prove I/O exactness.

Only after the startup boundary has separately been resolved, the README's fresh-run `--year 2026 --stage build|render|compare|all` commands can exercise the current partial pipeline. They **do not reproduce the full requested matrix** yet. No successful build/render is promised by this report.

next:
- Resolve why the exact 2026 executable still shows crash recovery before `-r` execution; inspect startup state in a separately authorized session. Do not retry blindly or force-kill AE.
- Validate all three no-effect I/O round trips, including premultiplication and FLOAT channels; verify Preserve-RGB/output settings.
- Implement three exact corpus cases per plugin, same-bundle F47d/F51 host renders and raw comparison. Cache index identifies F47 as load-only; F51 is the existing standalone F47d rendering bridge. Bind inputs, params and installed hashes explicitly.
- Obtain fresh AE popup readbacks/Effect Controls evidence; investigate host/InData differences only after exact I/O controls. No full-matrix completion or bit-exact output claim is made.

cleanup:
- Stopped at the ticket's mandatory GUI timeout boundary. No further AE launch/render was attempted. No worker remains running; no AE main process was observed at final check.
- Ticket scratch was 56 MiB before cleanup, below 5 GiB. Removed regenerable venv and Python caches; kept logs, generated inputs and launch script in scratch. Durable evidence is committed, not dependent on scratch survival. Installed bundles remain in place.
