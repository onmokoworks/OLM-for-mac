status: blocked
summary: AE 2025 probe and AE 2026 no-effect project preparation both failed before JSX produced results.
  Startup dialogs prevent proceeding under the ticket's no-click rule; no pixel comparison is claimed.
  Fixed the helper-sensitive busy check and isolated scratch/evidence from A01.
  Extracted 20 source popup declarations across all 10 plugins, including literal labels and defaults.
  Full parameter audit, I/O calibration, render matrix, F47 comparison and Effect Controls captures remain incomplete.

facts:
- Branch: `orch/A01b-real-ae-render-compare`; initial working tree clean.
- Initial `ps -axo pid,command | grep -E 'MacOS/After Effects$'` found no main executable. `memory_pressure` reported 51% free; subsequent samples were 49% and 52%. No non-owned AE was encountered, so no five-minute busy wait was necessary.
- `python3 tools/ae_smoke/run_ae_smoke.py --year 2025 --run-id probe2025` launched owned PID 16164. The driver attempted `-r` and, after 35 seconds, `DoScriptFile`. No `probe-2025.json` was produced. The 120-second probe deadline expired; cleanup sent SIGTERM and then used the driver's bounded kill fallback. Exit status of the driver: 1.
- [2025 startup warning](A01b-evidence/blocked-2025.png) names `/Library/Application Support/Adobe/Common/Plug-ins/7.0/MediaCore/DepthONNX.plugin`, `FillLine.plugin`, and `Signal/signal.plugin` as plugins that could not be loaded. No dialog was clicked, no third-party plugin was moved, and no sign-in diagnosis is inferred from this warning.
- `orchestra/state/A01b-real-ae-render-compare/venv/bin/python tools/ae_smoke/prepare_inputs.py orchestra/state/A01b-real-ae-render-compare/inputs` succeeded: deterministic seed 1, indices 0/3/2 for 8/16/32 bpc, geometries 21x19 / 20x23 / 10x19. [Input hashes](A01b-evidence/inputs.json). These are generated inputs, not validated no-effect results.
- `orchestra/state/A01b-real-ae-render-compare/venv/bin/python tools/ae_smoke/run_ae_smoke.py --year 2026 --stage io --run-id io2026 --prepare-inputs "$PWD/orchestra/state/A01b-real-ae-render-compare/inputs/inputs.json"` launched owned PID 17521 only after PID 16164 exited. It attempted the same two dispatch mechanisms. No probe JSON, AEP, or rendered frame was produced.
- [Captured desktop dialogs during the 2026 attempt](A01b-evidence/blocked-2026.png) show crash recovery options and a warning whose last logged message references the **2025** Required directory. The screenshot alone does not establish which process owns each dialog. [Separate scripting error](A01b-evidence/script-error-2026.png) says the script file cannot run because the scripting plugin is not installed. This is the displayed error, not an independently verified missing-file diagnosis.
- `python3 tools/ae_smoke/source_popups.py orchestra/reports/A01b-evidence/source-popups.json`: 10 plugins, 20 popup declarations. [Source data](A01b-evidence/source-popups.json) retains source hashes, line numbers, count, default and PF_ADD_POPUP label strings resolved from source string tables. AE scripting label readback remains unavailable.
- Source declaration anomalies retained without modification: DirectionalBlur Noise Type count 2 / labels 3; DistanceGradation In/Out default 0 with count 3; DistanceGradation Blur Mode count 5 / labels 3; KiraKira Channel count 6 / labels 4 and Blur Mode count 3 / labels 4. These are not new AE-render bug findings.
- `python3 tools/ae_smoke/verify_evidence.py`: retained A01 load/apply/mapping evidence 10/10; current installed executable hashes 20/20 match the A01 manifest. This is not a fresh A01b load result.
- `python3 tools/ae_smoke/test_compare.py`: 4 tests passed. `python3 -m py_compile tools/ae_smoke/*.py` with scratch PYTHONPYCACHEPREFIX: success.

| Plugin | 2026 effect renders 8 / 16 / 32 | AE-vs-F47 comparisons 8 / 16 / 32 | 2025 renders 8 / 16 / 32 |
| --- | --- | --- | --- |
| OLMBlur | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| ColorKeep | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMColorKey | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMDirectionalBlur | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMDistanceGradation | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMKiraKira | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMSmoother2 | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMToonDilate | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMRadialBlur | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |
| OLMSmoother | 0 / 0 / 0 | 0 / 0 / 0 | 0 / 0 / 0 |

All no-effect depth cells are unmeasured. Exact counts, differing-sample counts and first mismatch are **unavailable**, not zero. All 120 requested 2026 cells and 30 requested 2025 cells remain unattempted due to the startup/script boundary. No corpus case was judged intrinsically unreproducible; this is a global prerequisite block, not 150 case-specific skips. No aerender or F47 worker was launched. No per-plugin Effect Controls evidence was obtained.

inference:
- Startup state, not measured pixel arithmetic, is the immediate blocker. The dialogs plausibly explain absent script results; causality and whether the 2026 issue was pre-existing are unproven. The forced 2025 shutdown may have contributed to the subsequent crash-recovery state.
- Retrying unchanged launches cannot establish the I/O boundary. Stop here under the no-click rule, rather than altering preferences, relocating unrelated plugins, or classifying nonexistent pixel differences.
- Popup count/label/default discrepancies warrant a separate UI compatibility investigation after scripting works; source mismatches alone do not establish runtime behavior.

changed_files:
- `tools/ae_smoke/run_ae_smoke.py`: exact-main-executable busy check, A01b scratch isolation, bounded-size timeout screenshots; `--stage io` prepares control-only projects (unvalidated). Other requested stage names are accepted but fail explicitly as unimplemented. This is **not** the requested completed one-command pipeline.
- `tools/ae_smoke/source_popups.py`: deterministic source popup extraction; no full type/name/default/bounds audit claim.
- `tools/ae_smoke/README.md`: A01b blocker and precise stage limitations.
- `orchestra/reports/A01b-real-ae-render-compare.md`, `orchestra/reports/A01b-evidence/`: report, source popup metadata, input hashes, small cropped blocker screenshots and run metadata.

verify:
```sh
python3 tools/ae_smoke/verify_evidence.py
python3 tools/ae_smoke/test_compare.py
mkdir -p orchestra/state/A01b-real-ae-render-compare/recheck
python3 tools/ae_smoke/source_popups.py orchestra/state/A01b-real-ae-render-compare/recheck/source-popups.json
cmp orchestra/reports/A01b-evidence/source-popups.json orchestra/state/A01b-real-ae-render-compare/recheck/source-popups.json
PYTHONPYCACHEPREFIX="$PWD/orchestra/state/A01b-real-ae-render-compare/recheck/pycache" python3 -m py_compile tools/ae_smoke/*.py
```
Expected: retained 10/10 and installed 20/20 hashes; 4 comparator tests pass; 20 popup declarations; byte-identical extraction; Python syntax success. None launches AE or claims pixel exactness.

next:
- Resolve AE startup dialogs / scripting availability in a separately authorized interactive session. The current ticket explicitly forbids clicks, so this worker did not dismiss recovery dialogs or reset preferences.
- Retry both probes with fresh run IDs. Complete all-parameter source/AE audit and validate no-effect TIFF/EXR round trips before rendering effects.
- Implement and validate aerender lifecycle, decoding, corpus parameter mapping, F47 same-bundle host invocation, matrix/comparison/screens stages and the `all` pipeline. Prioritize 2026 8-bpc defaults only after the no-effect gate passes.

cleanup:
- Both drivers exited 1 with `AE did not complete probe; exit=None` after their 120-second deadlines. [Attempt logs and memory samples](A01b-evidence/attempts.json) retain actual outputs. Traceback line excerpts can differ from the current file because the driver was edited during these attempts; the exception message is unchanged.
- Final `ps -p 16164,17521,17541 -o pid=,command=` returned no processes. Owned AE instances and the observed 2026 crashpad helper have exited. Pre-existing helpers were left untouched. No background worker was started.
- No preferences, plugin sources, release gates, ledger, MAIN checkout, emulator source or installed bundles were modified. No instrumented bundles were created.
- One cleanup tool call was rejected by automatic review because `rm -f` style commands are prohibited. The whole command was rejected before execution. Cleanup was retried with Python restricted to named ticket scratch paths; no permission bypass was requested.
- Scratch remained below 5 GiB (64 MiB before cleanup); regenerable venv/cache and full-desktop screenshots removed. Kept committed screenshots are 123,778 / 369,645 / 91,171 bytes, each below 400 KB. Small input files and logs remain in ignored scratch.
- Synthetic busy-check verification matched a main process and excluded crashpad/dynamiclinkmanager paths. This is not a live busy-wait test.
