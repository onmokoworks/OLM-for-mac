# A01: real After Effects smoke test of the 10 Mac `.plugin` bundles (headless, scripted)

## Why
- Every exactness result so far comes from our own hosts: the AEXCompat fake AE host, and the F47 native-plugin host.
- Real After Effects has never loaded a bundle. This ticket checks five things:
  - whether real AE loads each of the 10 bundles;
  - whether their params show up as declared;
  - whether they render in 8, 16 and 32 bpc on the Smart route without errors;
  - whether AE's output equals our F47 native-plugin host output for the same input and params;
  - whether x86_64 (Rosetta) matches.
- Use only scripting: ExtendScript plus `aerender`. Do not use GUI clicking. Any GUI-only check goes in a screenshot that the orchestrator looks at.

## Environment (facts)
- AE 2026: `/Applications/Adobe After Effects 2026/`. It contains `Adobe After Effects 2026.app`, `aerender` and `Plug-ins/`.
- AE 2025 is installed alongside it.
- The `Plug-ins/` folders are owned by root. The user creates user-owned subfolders once:
  - `/Applications/Adobe After Effects 2026/Plug-ins/OLM-smoke/`
  - `/Applications/Adobe After Effects 2025/Plug-ins/OLM-smoke/`
- If those folders are missing or not writable, stop immediately. Report `blocked: needs user sudo` with the exact command.
- **Never** write anywhere else under `/Applications` or `/Library`. Use no sudo.
- The user may also be using AE. Before launching AE, check with `pgrep -f "After Effects"`. If AE is already running, wait (poll every 5 min, up to 2 h). Never kill an AE process you did not start.

## Do
1. **Fresh bundles.**
   - Build all 10 from HEAD with `tools/fuzz/build_F47_bundles.py` into scratch under `~/.cache/olm-emu/A01/`. This must be HEAD, because the DistanceGradation deployment target changed after I03.
   - Confirm each is Universal with minos 11.0 (`lipo -info`, `vtool -show-build`).
   - Copy them into both `OLM-smoke/` folders.
2. **Scripting setup.**
   - Run JSX with the app's `-r <script.jsx>` flag, or `osascript ... DoScriptFile`. Choose whichever works headless-ish.
   - If the "Allow Scripts to Write Files" preference is needed, set it in the user prefs file only after backing it up, and restore the backup at the end.
   - Detect and handle first-launch dialogs (home screen, crash recovery) by script or prefs. If a modal blocks you, take a `screencapture` and report it rather than clicking.
3. **Load check (JSX).**
   - Enumerate `app.effects` and confirm all 10 match names, taken from each PiPL. List any that are missing.
   - For each plugin, apply it to a solid. Dump every param: name, type, default, min/max, and popup items. Diff that dump against the param declarations in source (PF_ADD_* in `mac/*/`).
4. **Render matrix.**
   - Build inputs from the fuzz input generator. Use the same deterministic patterns the adapters use, written as 16-bit PNG/TIFF and 32-bit EXR. Turn color management off (no working space; linearize off).
   - Make one comp per plugin per depth (8/16/32 bpc): the default params, plus 3 param sets taken from existing exact corpus cases of that plugin.
   - Render with `aerender` to lossless TIFF (8/16) or EXR (32, uncompressed float). Record any errors, and the time per frame.
5. **Compare against our host.**
   - Run the F47 native-plugin worker on exactly the same input pixels and params, using the same `.plugin` bundle.
   - Compare AE output with that host output pixel by pixel, after converting AE's file to the host's pixel layout (ARGB, AE 16-bit range 0..32768).
   - Classify every difference in one of these categories:
     - file I/O or format conversion (e.g. 16-bit scaling, premultiplication, alpha mode);
     - color management;
     - an InData/host difference (layer size, downsample, `extent_hint`, `pixel_aspect`, field, and so on);
     - a real plugin bug.
   - Exact equality on the I/O-faithful cases is the goal. If a difference is a host difference, record the AE value. A scratch-only instrumented build that logs in_data/params/world fields is allowed, but install it only into `OLM-smoke/` under a different match name, never commit it, and remove it afterwards.
6. **Rosetta.** Run AE 2026 under `arch -x86_64` if AE supports it (it may not launch under Rosetta). If it does, repeat step 4 for the default and one param set, and compare with the arm64 renders.
7. **AE 2025.** Repeat steps 3 and 4 with the default params only, as a compatibility check.
8. **Interactive-only checks.**
   - Open one comp per plugin in the GUI and take a `screencapture` of the Effect Controls panel. Save the files under `orchestra/reports/A01-evidence/screens/`.
   - Do not click anything. The orchestrator reviews the screenshots.
9. **Cleanup.**
   - Quit AE (only the instance you started).
   - Leave the bundles in `OLM-smoke/` so the user can try them. List the exact paths.
   - Restore any pref you changed.

## Deliverables
- `orchestra/reports/A01-real-ae-smoke.md` with:
  - a per-plugin table: loaded, params OK, and render status 8/16/32 bpc;
  - AE vs host results: exact / differs, with classification;
  - Rosetta and AE 2025 results;
  - the screenshot list.
- Put scripts in `tools/ae_smoke/` (JSX, a driver `run_ae_smoke.py`, and a compare script) so the user can rerun everything with one command. Commit them.
- Do not change plugin sources. Report suspected plugin bugs with a minimal repro.

## Rules
- Use 1-2 processes, and at most one AE instance at a time. Check `memory_pressure` before launching AE and keep at least 30% free.
- Do not touch the release gate/ledger.
- The stop rule applies. Partial progress is valuable, e.g. "loads plus renders 8 bpc for all 10".
