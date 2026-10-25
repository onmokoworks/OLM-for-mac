status: blocked
summary:
- Fixed EXR input interpretation using the existing SHA-256-bound Preserve RGB footage template.
- Fresh 32 bpc Full controls at 1920x1080 and 1279x719 are both raw exact (0 differing samples).
- GUI watcher rejected the workspace titled KBar; mandatory unknown-dialog stop applies. No click or forced termination.
- Retained measurements actually show 107/120 priority effect comparisons exact, not A02f's reported 108/120.
- Depth/corpus effect campaign and straight-alpha ColorKeep confirmation remain incomplete.

facts:
- Read AGENT_GUIDE, A01c/A02f reports, ae_smoke README, GOTCHAS and the plugin forbidden-action table. No plugin source, installed bundle, MAIN, ledger or release gate changed.
- `ioreg -n Root -d1` showed a logged-in on-console session without a lock key; no AE/aerender main executable was running. `memory_pressure` reported 58% free before work.
- Existing 32 bpc EXR has separately named A/B/G/R FLOAT32 channels; alpha=1. First source R=0.125490203499794, exported R=0.42113351821899414. Old Full control had 6,220,800 differing samples; first R bytes d09ed73e versus 8180003e. Therefore HALF truncation or alpha multiplication cannot account for this opaque control mismatch. No decoder compensation was added.
- New input template hash: `51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679`. EXR footage is replaced within this existing template; queue is cleared, alpha set straight, project settings retained, and template provenance recorded. TIFF priority generation remains unchanged.
- Build command below exited **1**: watcher recorded `Unknown AE dialog; no click` for window 1863, title KBar. The screenshot shows the workspace. JSX nevertheless saved four projects, 176 queue items, phase=complete, and AE exited normally. Both preference files restored with matching original/restored hashes. Evidence: [build log](A02g-evidence/build.log), [dialog log](A02g-evidence/dialogs.jsonl), [119 KB screenshot](A02g-evidence/unknown-1863.png), [manifest](A02g-evidence/build.json), [preference record](A02g-evidence/prefs.json).
- Procedural deviation: the calibration render was launched after seeing phase=complete and no AE process, before inspecting the build exit-1 log. On discovering the watcher failure, wrote a cooperative stop file. Both control renders had already finished normally (exit 0); no further AE launch was made. Future resume MUST inspect the build process exit status as well as marker and process absence.
- Calibration command exited 0, two outputs, no refusals. Raw comparison: 1080p SHA-256 `618d0e65f8c901e8e5f9fabdcf341aca312ce6fcea8b333908e6b9216c44c07a`; odd-size `23f683d2351c097fb00b391ad3466369ca73eb502092a1f5199237c7ba5aa2dd`. Both 0 differing samples, first mismatch null. [Comparisons](A02g-evidence/calibration-comparisons.json), [render records](A02g-evidence/calibration-render-results.json).
- Retained A02f depth checkpoint contains 110 renders: all 88 16 bpc items and 22 32 bpc items. 16 bpc effects: 72/80 raw exact, eight ColorKeep hidden-RGB export differences. Two Full 16 bpc controls exact; six reduced controls are resampling proxies. No 32 bpc effects promoted from the uncalibrated old projects.
- Correction to A02f narrative: retained priority comparisons contain **107 exact + 12 ColorKeep hidden-RGB differences + one unresolved Smoother difference**. Full 4K Smoother differs in two samples; first (1649,1235), B, AE=de, bundle=df. AE SHA-256 `c9742d1378262bab8d398f543687d1702a973a78381bd10a2bb870c960edd109`, host `14c5a995110525b5c04c2c8a86c20ea8904a580bb92256bbb7fb0608fe7e7531`. This is retained data, not a newly repeated render or proven plugin bug.
- `test_compare_downsample.py`: 2 tests pass; `test_pipeline.py`: 7 tests pass. Python syntax checks and `git diff --check` pass. Final AE/aerender main executable check: none. No owned background task remains.

inference:
- Exact fresh controls support EXR import interpretation as the old 32 bpc I/O cause. Output channel ordering and float preservation were already correct.
- KBar appears to be a workspace-title false positive, but no broad dialog allowlist bypass was made. Watcher repair needs a separate bounded follow-up.
- ColorKeep's 20 available 8/16 bpc differences are confined to hidden RGB at zero alpha; the 16 bpc EXR is also premultiplied, so it does not establish straight-alpha preservation. DistanceGradation's available black 8/16 bpc defaults match the reference; black alone is not a plugin error.
- All effect comparisons still use reduced control pixels and queue-resolution ratios as input/geometry proxies, not a live InData trace. Full-4K uses same-bundle host fallback. Do not generalize these results to the missing PF32/corpus cells or native Windows AE.

changed_files:
- tools/ae_smoke/run_ae_smoke.py
- tools/ae_smoke/prepare_downsample.jsx
- tools/ae_smoke/summarize_retest.py
- tools/ae_smoke/README.md
- orchestra/reports/A02g-real-ae-retest-downsample.md, A02-real-ae-retest-downsample.md, A02g-evidence/

verify:
```sh
# Offline, no AE launch; retained evidence is committed.
python3 tools/ae_smoke/summarize_retest.py orchestra/reports/A02f-evidence/priority --depths orchestra/reports/A02g-evidence/retained-depths
TMPDIR="$PWD/orchestra/state/A02g-real-ae-retest-downsample" PYTHONDONTWRITEBYTECODE=1 '../A02f-real-ae-retest-downsample/orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python' tools/ae_smoke/test_compare_downsample.py
git diff --check
```
Expected: tables below, two tests pass, no whitespace errors. The venv belongs to the retained A02f worktree; alternatively use a numpy/tifffile/OpenEXR environment.

Exact live commands executed (do not retry build with its existing run ID):
```sh
PYTHONDONTWRITEBYTECODE=1 '../A02f-real-ae-retest-downsample/orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python' tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-depths --stage build --run-id depths-g1 --scratch orchestra/state/A02g-real-ae-retest-downsample
PYTHONDONTWRITEBYTECODE=1 '../A02f-real-ae-retest-downsample/orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python' tools/ae_smoke/run_ae_smoke.py --year 2026 --matrix downsample-depths --stage render --run-id calibration-g1 --scratch orchestra/state/A02g-real-ae-retest-downsample
PYTHONDONTWRITEBYTECODE=1 '../A02f-real-ae-retest-downsample/orchestra/state/A02f-real-ae-retest-downsample/venv/bin/python' tools/ae_smoke/compare_downsample.py orchestra/state/A02g-real-ae-retest-downsample/calibration-g1
```
Calibration manifest selected only Full controls from the two 32 bpc projects. New builds require a fresh run ID after the watcher boundary is resolved; the existing committed builder reproduces the template and input generation.

next:
- A03 follow-up: classify the already-recognized workspace when its same window ID changes title to KBar; preserve fail-closed unknown alerts, add screenshot/window-transition regression tests. Require successful builder exit before any render.
- A02h: rerun corrected 32 bpc defaults (including untouched DistanceGradation), build/render 20 unchanged corpus witnesses, verify input controls per corpus, preserve exact parameter readbacks, acquire live InData geometry if differences remain.
- ColorKeep export ticket: choose and read back straight-alpha output, calibrate transparent nonzero RGB; rerender defaults at all resolutions. Do not modify plugin arithmetic to repair export loss.
- Smoother 4K isolation ticket: reproduce the two retained differences using the original A02e 8 bpc 3840x2160 project, queue item for OLMSmoother Full, deterministic input, and recorded same-bundle host. Obtain input/host boundary evidence before classifying a plugin bug.
- DistanceGradation 8/16 black defaults need no fix based on current exact data; PF32 defaults remain untested by the calibrated campaign.

E=raw exact; H=hidden-RGB I/O difference; U=uncalibrated/unresolved; P=rendered, comparison pending; —=not rendered. B suffix=black/transparent. Each cell lists counts across available sizes. No tolerance is used.

| Plugin | 8 Full/Half/Third/Quarter | 16 Full/Half/Third/Quarter | 32 Full/Half/Third/Quarter |
|---|---|---|---|
| OLMBlur | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1U / 1P / — / — |
| ColorKeep | 3HB / 3HB / 3HB / 3HB | 2HB / 2HB / 2HB / 2HB | 1UB / 1PB / — / — |
| OLMColorKey | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1U / 1P / — / — |
| OLMDirectionalBlur | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1U / 1P / — / — |
| OLMDistanceGradation | 3EB / 3EB / 3EB / 3EB | 2EB / 2EB / 2EB / 2EB | 1UB / 1PB / — / — |
| OLMKiraKira | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1U / 1P / — / — |
| OLMSmoother2 | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1P / 1P / — / — |
| OLMToonDilate | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1P / 1P / — / — |
| OLMRadialBlur | 3E / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1P / 1P / — / — |
| OLMSmoother | 2E,1U / 3E / 3E / 3E | 2E / 2E / 2E / 2E | 1P / 1P / — / — |

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

cleanup:
- Scratch is 199 MiB; regenerable Swift module cache and Python caches removed.
- All retained screenshot files were reduced below 400 KB. No installed bundles or shared reference assets changed.
- Saved scratch projects are reproducible through the committed builder and existing template; they are not published reference oracles.
