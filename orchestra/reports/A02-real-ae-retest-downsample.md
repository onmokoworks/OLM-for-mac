status: partial
summary:
- Completed 176/176 depth renders and attempted all 20 corpus witnesses plus eight straight-alpha probe frames.
- Depths: 136/160 effects raw exact vs original; 16 ColorKeep hidden-RGB differences; eight Smoother v1 PF32 reference limitations.
- Straight PNG confirms ColorKeep hidden-RGB export loss at all four tested 8 bpc resolutions: 4/4 raw exact vs original.
- Corpus: eight exact, two hidden-RGB differences, nine I/O-blocked comparisons, one real-AE Smoother2 refusal; three parameter readbacks also differ.
- KBar watcher repair is live-verified. No plugin sources/bundles, MAIN, ledger or release gate changed.

facts:
- Branch `orch/A02h-real-ae-retest-downsample`. Read A01c/A02f/A02g reports, AGENT_GUIDE, ae_smoke README, GOTCHAS, plan and per-plugin forbidden-action table. Initially unlocked, no AE main process, memory 57% free. All launches used AE 2026 by full path and serial execution.
- Copied only A02g's completed four-project manifest into `depths-h1`; reused its AEP/footage paths. Render stage exited 0: **176/176 outputs, zero errors/refusal tags**. Four Full controls are raw exact; reduced controls remain resampling proxies. [Depth evidence](A02h-evidence/depths/comparisons.json).
- Full 32 bpc control at 1080p: zero differing samples, SHA-256 `618d0e65f8c901e8e5f9fabdcf341aca312ce6fcea8b333908e6b9216c44c07a`. Untouched DistanceGradation 32 bpc defaults are raw exact vs F53 at both sizes and all four resolutions, including their transparent black output.
- 16 bpc effects: 72 exact, eight ColorKeep hidden-RGB differences. 32 bpc effects: 64 exact, eight ColorKeep hidden-RGB differences, eight unavailable Smoother v1 references. ColorKeep 1080p PF32 exceeded F53's guest arena; F53 bundle host lacked the ordinary float iterate callback. Cached V01's F51/F47d full-frame transport rendered the same installed bundle. First difference: (0,0), R, AE `00000000`, reference `8180003e`; 6,220,800 differing samples. Other available depth references use F53 original AEX.
- Smoother v1 original rejects PF32: `AEX did not advertise support for output argb32f or input argb32f pixel depth`; native direct-PF32 host returns 516. AE itself produces images. No direct PF32 exactness claim is made; AE's callback depth was not traced.
- Fresh `remaining-h1` GUI build exited 0, phase=complete, 21 projects/48 queue items, zero watcher clicks, clean AE exit. KBar no longer triggers unknown-dialog failure. Both GUI preference files restored byte-exactly. Across GUI and 224 aerender attempts, **225/225 preference lifecycle records restored**. [Watcher log](A02h-evidence/dialogs.jsonl), [restore audit](A02h-evidence/preference-restores.json).
- Applied existing `_HIDDEN X-Factor 8`; AE readback: `PNG Sequence`, `Straight (Unmatted)`, `Millions of Colors+`, `RGB + Alpha`. At 1279×719, ColorKeep defaults match original AEX at Full/Half/Third/Quarter with zero differing samples, including nonzero RGB under zero alpha. Full raw SHA-256 `65993f33a74fddc527d0beb2c931095dc6e42b8430b203796de3c2fdd88bc876`. Full input control is exact. This confirms export loss for the paired 8 bpc TIFF/PNG test; the transparent images are expected, not a refusal.
- All 20 corpus source files and pixels were hash-checked, without editing their values. Their Full resolution/depth is retained. Four 1×1 witnesses use a 4×4 comp, top-left original layer and output crop; actual output is 1×1. Corpus import reads back premultiplied-black interpretation. Ten of 20 controls are exact. Ten fail I/O; nine effect comparisons are withheld and one effect independently refuses.
- Four 16 bpc controls cannot be decoded as exact integer/32768: DirectionalBlur corpus2 (102 samples; first B at (0,0), EXR word `9053cb3e`, scaled value 13012.890625), KiraKira corpus2 (922), Smoother2 corpus2 (416), RadialBlur corpus1 (28). These are retained codec boundaries, never rounded. Other I/O failures include zero-alpha RGB loss and floating-point changes. ColorKey's two exact-input corpus effects differ only in hidden RGB: 93 and 183 samples, first R at (1,0), AE `0000`, reference `8e0d`.
- **17/20 corpus parameter readbacks are exact.** DirectionalBlur corpus2 and RadialBlur corpus1/2 also have AE parameter quantization differences; full requested/observed values are in [readback audit](A02h-evidence/remaining/corpus-parameter-check.json). Their I/O already fails, so they are not promoted as exact corpus replays.
- **Real-AE error:** Smoother2 corpus1, 11×8 PF8, `seed1_case000067_65ee3b1d9cdf.json`, queue index 2. aerender returns 0 but creates no image; trace `SmartRender:smartrender-decoded-colors@5403`. Its 25 predecessors succeeded. The campaign stopped; no failed frame was retried. Remaining unattempted projects were split into fresh `remaining-h2` (two items) and `remaining-h3` (20 items), both exit 0. Total: **47/48 remaining outputs, one refusal**. [Error log](A02h-evidence/smoother2-refusal.aerender.log).
- The same Smoother2 source pixels/parameters replay through F53 and the installed bundle's full-frame host with **zero differing samples**, raw SHA-256 `47794b301c518d0c409b12fbe9909cf5b298a23a2893b35504d207b536106247`. Installed binary SHA-256 `32056e8cc5fc346421cf977e3a61c784707fa122f43a4f7339592e187f928b45`. This diagnostic uses packed worlds, not the corpus padding contract. [Replay](A02h-evidence/smoother2-full-replay.json). An earlier shared-arena fuzz replay had original=ok but native=`worker did not execute native selectors`; it is retained as a harness failure, not a plugin result.
- Watcher 17, pipeline 7, render 2 and codec 3 dedicated tests pass. Generic unittest discovery had 11 errors because the watcher binary requires CLI initialization; the failed invocation is retained. Codec rejection initially stopped comparison; it now records the precise boundary and continues without converting samples.
- Historical 8 bpc priority evidence is reused, not rerendered: 132/132 outputs; **107/120** raw exact, 12 ColorKeep hidden-RGB differences, one Smoother Full-4K two-sample difference assigned to S01. The earlier 108/120 narrative was incorrect.

inference:
- Smoother2's real-host failure is localized to `DecodedColorsMatch`: it byte-compares AE's floating color suite result with legacy 8-bit color components divided by 255. The refusal tag proves this guard rejected; the exact disagreeing suite component has not been captured. This is a host-integration/plugin admission bug candidate, not evidence to change core pixel arithmetic.
- The paired straight-PNG result confirms the ColorKeep 8 bpc export explanation for this odd-size input at four resolutions. It does not prove 16/32 bpc hidden-RGB fidelity or all transparency/compositing profiles.
- Corpus control failures are I/O boundaries, and the three parameter changes are host materialization boundaries. They do not establish algorithm bugs. Smoother v1 PF32 likely involves AE depth negotiation, but actual callback depth is unconfirmed.
- Queue Resolution readbacks and decoded output dimensions are measured. Inputs to reduced reference renders are no-effect output proxies; origin/full extent and callback geometry are assumptions. No live InData trace was added and no native Windows AE claim is made.

changed_files:
- tools/ae_smoke/ae_dialog_watch/Policy.swift, test_watch.py
- tools/ae_smoke/{run_ae_smoke.py,prepare_downsample.jsx,corpus_inputs.py,render_downsample.py,compare_downsample.py,test_compare_downsample.py,summarize_retest.py,replay_full_corpus.py,README.md}
- orchestra/reports/A02h-real-ae-retest-downsample.md, A02-real-ae-retest-downsample.md, A02h-evidence/

verify:
```sh
# Offline retained tables; no AE launch.
python3 tools/ae_smoke/summarize_retest.py orchestra/reports/A02f-evidence/priority --depths orchestra/reports/A02h-evidence/depths
# Recreate an environment with numpy, tifffile, OpenEXR, Pillow if scratch was removed.
export TMPDIR="$PWD/orchestra/state/A02h-real-ae-retest-downsample"
export PYTHONDONTWRITEBYTECODE=1
python3 tools/ae_smoke/ae_dialog_watch/test_watch.py --scratch "$TMPDIR/watch-recheck"
"$TMPDIR/venv/bin/python" tools/ae_smoke/test_pipeline.py
"$TMPDIR/venv/bin/python" tools/ae_smoke/test_downsample.py
"$TMPDIR/venv/bin/python" tools/ae_smoke/test_compare_downsample.py
"$TMPDIR/venv/bin/python" tools/ae_smoke/replay_full_corpus.py tests/fuzz_corpus/olmsmoother2/seed1_case000067_65ee3b1d9cdf.json "$TMPDIR/smoother2-recheck-fresh"
git diff --check
```
Expected: tables below; 17/7/2/3 tests pass; standalone Smoother2 replay exits 0 with exact=true and the raw hash above; no whitespace errors. The replay directory must be new.

Live commands actually used (saved projects/absolute paths must still exist; do not repeat a build ID):
```sh
# All commands use the ticket-local venv, TMPDIR and PYTHONDONTWRITEBYTECODE above.
"$TMPDIR/venv/bin/python" tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-depths --stage render --run-id depths-h1 --scratch "$TMPDIR"
"$TMPDIR/venv/bin/python" tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-remaining --stage build --run-id remaining-h1 --scratch "$TMPDIR"
"$TMPDIR/venv/bin/python" tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-remaining --stage render --run-id remaining-h1 --scratch "$TMPDIR"
"$TMPDIR/venv/bin/python" tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-remaining --stage render --run-id remaining-h2 --scratch "$TMPDIR"
"$TMPDIR/venv/bin/python" tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-remaining --stage render --run-id remaining-h3 --scratch "$TMPDIR"
# Comparisons were run for depths-h1 and remaining-h1/h2/h3:
"$TMPDIR/venv/bin/python" tools/ae_smoke/compare_downsample.py "$TMPDIR/depths-h1" --timeout 15
```
Build exited 0. depths-h1/h2/h3 render exited 0; remaining-h1 render exited 1 for the observed missing-image/refusal. The reports retain the merged 48-item measurements; original projects and input paths are in the manifest.

next:
- **S02: Smoother2 real-AE floating color decode refusal.** Minimal case is the named 11×8 PF8 corpus, unchanged parameters (all read back exactly), saved project `OLMSmoother2-corpus1-11x8-8.aep`, queue 2. Reproduce with a fresh `downsample-corpus` build then isolate this project's control/effect pair using its completed manifest. Capture both `PF_GetFloatingPointColorFromColorDef` and legacy `PF_Param_COLOR` bytes at the guard before changing admission. Preserve zero-diff F53/installed-host replay. No plugin fix is made here.
- **A02i: transparent corpus I/O and parameter materialization.** Repair/calibrate ten non-exact controls, including the four fractional PF16 EXR boundaries. Reproduce the two ColorKey hidden-RGB results with a depth-preserving straight output. Preserve original corpus pixels/params; do not round or normalize them to produce a pass. Investigate or select independently valid AE-representable witnesses for the three readback differences.
- **A02j: Smoother v1 project-32/callback-depth trace.** Determine AE's negotiated input/output depth; compare the original at that actual callback depth. Do not treat direct-PF32 rejection as an AE render error.
- ColorKeep defaults: no visible-black plugin fix is supported by the paired straight-PNG proof; validate straight FLOAT output separately for PF16/PF32. DistanceGradation default black output matches original in every measured depth/resolution, so no fix ticket is justified. Tiny zero-input corpus black frames are likewise not refusals.
- **S01** retains the historical Smoother Full-4K two-sample issue. It was not investigated here.

O=raw exact vs original AEX; F=raw exact vs same-bundle fallback; E=raw exact with unspecified reference; H=hidden-RGB I/O difference; U=uncalibrated/unresolved; P=rendered, comparison pending; —=not rendered. B suffix=black/transparent. Each cell lists counts across available sizes. No tolerance is used.

| Plugin | 8 Full/Half/Third/Quarter | 16 Full/Half/Third/Quarter | 32 Full/Half/Third/Quarter |
|---|---|---|---|
| OLMBlur | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| ColorKeep | 3HB / 3HB / 3HB / 3HB | 2HB / 2HB / 2HB / 2HB | 2HB / 2HB / 2HB / 2HB |
| OLMColorKey | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| OLMDirectionalBlur | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| OLMDistanceGradation | 2OB,1FB / 3OB / 3OB / 3OB | 2OB / 2OB / 2OB / 2OB | 1FB,1OB / 2OB / 2OB / 2OB |
| OLMKiraKira | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| OLMSmoother2 | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| OLMToonDilate | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| OLMRadialBlur | 2O,1F / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 1F,1O / 2O / 2O / 2O |
| OLMSmoother | 2O,1U / 3O / 3O / 3O | 2O / 2O / 2O / 2O | 2U / 2U / 2U / 2U |

Wall seconds per 8 bpc Full frame, including aerender startup; single observations.

| Plugin | 1080p | 4K |
|---|---:|---:|
| OLMBlur | 6.210 | 7.239 |
| ColorKeep | 6.203 | 7.203 |
| OLMColorKey | 6.228 | 6.201 |
| OLMDirectionalBlur | 6.207 | 6.328 |
| OLMDistanceGradation | 6.220 | 7.249 |
| OLMKiraKira | 6.200 | 9.264 |
| OLMSmoother2 | 6.201 | 8.462 |
| OLMToonDilate | 6.214 | 8.349 |
| OLMRadialBlur | 6.216 | 8.435 |
| OLMSmoother | 6.218 | 8.269 |

The preceding default table retains the premultiplied baseline. The separate
ColorKeep straight-PNG probe is 1OB / 1OB / 1OB / 1OB at 8 bpc, 1279×719.
B means all RGB zero **or** all alpha zero; straight ColorKeep has nonzero RGB
and zero alpha. O/F distinguish original AEX and same-bundle reference paths.

Corpus Full-only results (E=exact vs original; H=hidden-RGB difference;
I=I/O blocks comparison; ERR=no frame/refusal). These are additional witnesses,
not resized or depth-converted substitutes for the defaults.

| Plugin | Corpus 1 (depth) | Corpus 2 (depth) | Parameter readbacks exact |
|---|---|---|---|
| OLMBlur | E (16) | E (16) | 2/2 |
| ColorKeep | I (32) | I (32) | 2/2 |
| OLMColorKey | H (16) | H (16) | 2/2 |
| OLMDirectionalBlur | I (32) | I (16) | 1/2 |
| OLMDistanceGradation | E (8) | E (16) | 2/2 |
| OLMKiraKira | I (8) | I (16) | 2/2 |
| OLMSmoother2 | ERR (8) | I (16) | 2/2 |
| OLMToonDilate | E (8) | E (16) | 2/2 |
| OLMRadialBlur | I (16) | I (8) | 0/2 |
| OLMSmoother | E (16) | E (16) | 2/2 |

Additional measured Full 1080p wall seconds, including aerender startup (single observations).

| Plugin | 16 bpc | 32 bpc |
|---|---:|---:|
| OLMBlur | 6.102 | 7.113 |
| ColorKeep | 6.080 | 6.116 |
| OLMColorKey | 6.122 | 6.102 |
| OLMDirectionalBlur | 6.127 | 6.073 |
| OLMDistanceGradation | 6.117 | 6.080 |
| OLMKiraKira | 6.119 | 7.094 |
| OLMSmoother2 | 6.115 | 6.075 |
| OLMToonDilate | 6.111 | 6.078 |
| OLMRadialBlur | 6.104 | 7.074 |
| OLMSmoother | 6.108 | 7.096 |

cleanup:
- All AE/aerender processes started by this ticket exited normally. No SIGTERM/SIGKILL was sent, and no owned background process remains.
- All 225 preference lifecycle records restored successfully. Installed plugins are unchanged.
- Regenerable Swift binaries/module caches and bytecode removed; scratch is 1.8 GiB, below 5 GiB. Retained evidence is JSON/logs, with no new PNG/EXR evidence over 400 KB. Saved scratch AEPs are reproducible through committed builders, not published oracles.
- Retained refusal display log has trailing whitespace trimmed; original and retained hashes are in `A02h-evidence/log-formatting.json`. The initial staged whitespace check identified only those aerender log spaces; the final full-ticket diff check passes.
