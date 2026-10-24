# A01b: real AE render matrix and pixel comparison with our host (continues A01)

## State (facts; read `orchestra/reports/A01-real-ae-smoke.md` and `tools/ae_smoke/README.md`)
- A01 built HEAD bundles and installed them into `/Applications/Adobe After Effects {2026,2025}/Plug-ins/OLM-smoke/`.
- AE 2026 registered and applied all 10 bundles, and vmmap binds them to OLM-smoke.
- The old MediaCore OLM copies are no longer present. The orchestrator moved them to `~/Library/Application Support/Adobe/Common/Plug-ins/7.0/OLM_port_external_backups/20261024_before_A01_mediacore/`, so only one copy of each match name exists now.
- **The user has signed in to AE 2025 since A01 ran.** The 2025 sign-in blocker should be gone.
- A01 stopped because of a user AE 2025 session. That session has ended.
- **Busy check:** match only the main executable. Use `ps -axo pid,command | grep -E 'MacOS/After Effects$'`.
  - Leftover helpers (`crashpad_handler`, `dynamiclinkmanager`, `TeamProjectsLocalHub`) have "After Effects" in their path. They do not count as a running AE.
  - If a real non-owned AE is running, wait (poll every 5 min, up to 2 h). Do not finalize early because of it.

## Do
1. **AE 2025 probe.** Rerun `run_ae_smoke.py --year 2025` (load/apply/param dump).
2. **Params.** Complete the source vs AE param comparison for all 10 plugins: type, name, default, bounds and popup labels.
   - Read popup labels from the source PF_ADD_POPUP strings.
   - In AE, read what scripting allows. If AE can't expose labels, say so.
3. **I/O control first.**
   - For each depth (8/16/32 bpc), render the input layer with **no effect**, using color management off, and compare it with the source pixels.
   - Fix the TIFF/EXR conversion (16-bit 0..32768 scaling, premultiplied vs straight alpha, EXR channel order) until the no-effect round trip is exact.
   - Only then are effect comparisons meaningful.
4. **Render matrix (AE 2026).** Use `aerender` on each of the 10 plugins in 8/16/32 bpc, with the default params plus 3 exact corpus cases (`tests/fuzz_corpus/<plugin>/`).
   - Map their params into AE property values. Cases with input size, layer setup or params that AE cannot reproduce get skipped, and each skip needs a reason.
   - Record render success, any errors and the time taken.
5. **Compare.** Run the F47 native-plugin worker on the same bundle, the same input pixels and the same params, then compare it with the AE output using `tools/ae_smoke/compare.py`.
   - Classify each difference: I/O conversion, color management, host/InData difference (downsample, extent/ROI, pixel aspect, buffer expansion via Smart pre-render `max_result_rect`, and so on), or a plugin bug.
   - For a host/InData difference, a scratch-only instrumented bundle is allowed, but only if it:
     - goes into `OLM-smoke/` under a different match name;
     - is never committed;
     - is removed afterwards.
   - Report exact counts per plugin and depth.
6. **AE 2025.** Run the default params at 8/16/32 bpc and compare them with the AE 2026 renders.
7. **Screenshots.** Use script to open one comp per plugin and select the layer, so that the Effect Controls panel shows the effect. Capture each one with `screencapture`. Do not click anything.
8. Make `run_ae_smoke.py` able to run the whole thing with one command: `--year`, `--stage probe|io|matrix|compare|screens|all`.

## Rules
- Keep at most one AE instance at a time, and only one you started. Check `memory_pressure` and stay above 30% free.
- Quit only the instances you own.
- Make no plugin source changes. Report suspected plugin bugs with a minimal repro.
- Do not touch the release gate or ledger.
- Leave the installed bundles in place. Keep PNG evidence small: crop or downscale it to at most 400 KB each.
- The stop rule applies. Partial results are valuable; prioritize I/O control, then 2026 defaults at 8 bpc for all 10 plugins, then the rest.
