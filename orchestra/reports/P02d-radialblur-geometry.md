status: done
summary:
- Restored Smart request/result geometry, float32 X downsample arithmetic, and output packing from original AEX instructions.
- Realistic seed 1: 88 exact / 12 unavailable; fresh seed 20261024: 93 exact / 7 unavailable; zero Mac-only refusals or mismatches.
- Default 300: all candidate output hashes and error codes unchanged on both routes; the extra oracle timeout rechecks exact.
- Old corpus: 60/61 saved results match; C46 retains its historical oracle failure with unchanged Mac output. Realistic corpus 181/181 matches after one oracle-timeout retry.
- Unit comparison: 6/70 files pass before and after; 64 historical failures retained. ASan/UBSan: 181/181 exact realistic outputs.

facts:

Original binary and instruction evidence (read-only MAIN disassembly):
- AEX SHA256 `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`.
- F52c worker SHA256 `4d0d729931da4567abb3d0f8cdbb8cbd00833b2bec545173dfdf9a96e6c67a9e`; reused from INDEX, never rebuilt.
- `0x180004010..40c9` forwards the incoming request to checkout and unions checkout result/max rectangles into PreRender output. The Mac previously replaced both with full-resolution composition bounds and rejected downsampled worlds.
- Point getter `0x18000de60..df18` calls `1a080`, then `1a190`: DOUBLE per-axis denominator/numerator multiplication undoes the host's sampled point coordinates. Caller `6dc8..6e40` subtracts source origins, forms FLOAT32 X numerator/denominator, scales FLOAT32 context+104 (Noise Thickness), and promotes that ratio to DOUBLE for both center coordinates. The corresponding typed callers repeat this sequence at `75d8..7650` and `7de8..7e60`.
- Zoom `57a4..5830` forms four Gaussian-table lengths from FLOAT32 Strength/Fade times the X ratio, truncating to integer. Rotation's angular control conversions at `46ec..47ab` do not apply this spatial ratio. Caller `6e45..6e67` tests the six original controls before scaling; a scaled-zero blur must still execute its polar processing.
- The initial world copy is called at `6d8f..6db3`. The PF16 output writer at `7344..7424` indexes the computed plane using OUTPUT width, starting at zero, and advances the destination using output rowbytes. It does not add the requested output origin. This packed-prefix behavior is retained; no-op renders instead preserve the initial copy's source row stride.

Commands and measured results:
- `python3 orchestra/reports/P02d-evidence/measure.py --label before`: seed 1/n100 baseline Smart E/M/R/U = **11/5/72/12**. U takes precedence over a candidate refusal; availability differs slightly from F52c's archived run. Index 1 reproduces PF16 word 2: original bytes `9334`, candidate `9434`, one differing word; original SHA256 `8f964308efd9b522cde6fa817e3d38bb48e66c91d4cd6668c62f5ffc82367196`, candidate `e50b60e43e9f6e6389932f4ca12e01cdf082cb307ebebe851afb5c070ecf285b`.
- Initial geometry implementation: seed 1 **87/0/0/13**. Fresh seed **92/1/0/7**. Fresh index 38 is PF16, source 203x211, request [37,11,64,161], all six blur controls zero. Packed publication incorrectly treated the copy as a blur: 15,139 words differed, first word 109, original `684d`, candidate `4d78`. Keeping source rows for the no-op copy closes this general boundary. The initial implementation is preserved as `P02d-evidence/initial-geometry.patch` (apply to the parent cpp with the final header's default-one scale member).
- Final `measure.py --label final-1 --seed 1 --save` and `--label final-20261024 --seed 20261024 --save`: **88/0/0/12** and **93/0/0/7** respectively, n100 each, realistic-v1, serial adapter. Full cases, raw hashes, output rectangles, provenance and unavailable-oracle diagnostics are retained in `P02d-evidence/final-*-results.jsonl`. No tolerance. Pixel aspect, extent hints, subrectangles, asymmetric downsample, and odd byte strides are carried by the sampler.
- Default `tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0`: baseline Smart **276 exact / 24 unavailable**, candidate **275 exact / 25 unavailable**. Both Classic **2 exact / 126 mismatch / 172 refusal**. **300/300 candidate output hashes and error codes identical on each route**; no candidate regression. Case 62's extra timeout is oracle-only; candidate SHA256 remains `d3d08c4296f99ebc15bfa4e2cb2d9c2dc9890e68802bbcc177a5187d08027042`.
- `python3 orchestra/reports/P02d-evidence/verify_boundaries.py`: 60-second oracle limit, default seed 1/index 62 and realistic fresh/index 38 both **exact**. Index 38 output SHA256 `e9e5ca57cebf8f150366ca67c6d6fc198d6c934d5e9d30e9677f7850ed9fcfa5`.
- One intermediate refactor dropped the existing `preserve_rgb_of_zero_alpha` request flag; the default fake host returned 710 for all 300 Smart calls. Restoring the flag resolved this before final validation. The failing intermediate run is not counted as a passing campaign.
- Existing corpus `run.py --replay tests/fuzz_corpus/radialblur`: **61 attempted, 60 saved comparison objects match**. `C46_seed1_case000280.json` retains the F52c report's prior oracle failure; Smart changes from exact to uncompared, with the **same candidate output hash**, and Classic refusal remains the same. See `P02d-evidence/replay-old.json`.
- Realistic corpus replay: **181 attempted, 180 saved results match** on the 10-second run; seed 1/index 62 had an oracle timeout. Replaying that one saved case with `--case-timeout 60` **matches the saved result exactly**, completing **181/181**. Both reports are retained.
- `OLM_TEST_JOBS=1 python3 orchestra/reports/P02d-evidence/unit_tests.py --label baseline` / `--label candidate`: baseline source/header read from commit `5bb598413d4a40fc8b23480c7bc3a1a6b036ff18` with `git show` and restored after the run; all **70** plugin test files attempted serially, including no-argument free-function tests. **6 files pass / 64 fail** on each version, **zero per-file exit-status changes**. `unit-summary.json` lists every historical failing file; `units-{baseline,candidate}.json` includes diagnostic tails. Historical source-hash/installed-identity/fixture and old numerical-admission assertions remain failures. The superseded full-frame-only geometry test was updated to check real PreRender callbacks preserving requested and expanded checkout rectangles; its two tests pass.
- `verify_sanitized.py`: **181/181** realistic corpus outputs match saved exact original hashes/rectangles under ASan/UBSan, including padded byte strides and ROI. No sanitizer error. Existing baseline/type3 sanitizer test files also pass before/after.

- `git diff --check`: passes. Final scratch is approximately 13 MiB; regenerable candidate/build trees removed at completion. No background process from this ticket remains.

inference:
- The observed refusals were caused by the full-resolution world gate and PreRender rectangle replacement. The PF16 numerical boundary was missing downsample arithmetic, not a final-word rounding problem.
- The fresh-seed failure distinguished the original suite copy's row layout from the blur writer's packed-plane layout. Preserving both explains the mismatch without coordinate-specific output changes.
- The sampled Smart contract is established against the original CPU AEX emulator, not native AE or every possible source-origin/allocator state. PreRender preserves expanded checkout bounds; the original sampled oracle clips requested expansion to source bounds. Outputs exceeding source dimensions remain outside this measured domain and retain a bounds guard to avoid reading beyond the computed plane.

changed_files:
- `mac/OLMRadialBlur/OLMRadialBlur.cpp`, `mac/OLMRadialBlur/OLMRadialBlur.h`
- `tests/test_olmradialblur_global_polar_smart_contract_20260820.py`
- `tests/fuzz_corpus/radialblur_realistic_P02d/*.json` (181 labelled Smart witnesses)
- `orchestra/reports/P02d-radialblur-geometry.md`, `orchestra/reports/P02d-evidence/*`

verify:

From this worktree, serially:

```sh
export TMPDIR="$PWD/orchestra/state/P02d-radialblur-geometry"
export PYTHONDONTWRITEBYTECODE=1 OLM_TEST_JOBS=1
mkdir -p "$TMPDIR"
python3 orchestra/reports/P02d-evidence/measure.py --label verify-seed1 --seed 1
python3 orchestra/reports/P02d-evidence/measure.py --label verify-fresh --seed 20261024
python3 tools/fuzz/run.py --plugin radialblur --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/verify-default" --corpus "$TMPDIR/verify-default-corpus" --report "$TMPDIR/verify-default.json"
python3 tools/fuzz/run.py --plugin radialblur --jobs 1 --replay tests/fuzz_corpus/radialblur --scratch "$TMPDIR/verify-old" --report "$TMPDIR/verify-old.json" --budget-minutes 40
python3 orchestra/reports/P02d-evidence/replay_realistic.py --plugin radialblur --jobs 1 --replay tests/fuzz_corpus/radialblur_realistic_P02d --scratch "$TMPDIR/verify-realistic" --report "$TMPDIR/verify-realistic.json" --budget-minutes 40 --case-timeout 60
python3 orchestra/reports/P02d-evidence/verify_boundaries.py
python3 orchestra/reports/P02d-evidence/unit_tests.py --label verify
python3 orchestra/reports/P02d-evidence/verify_sanitized.py
```

Expected: zero Smart mismatches/refusals for available realistic oracles; default output hashes/errors match `default-regression.json`; old corpus 60/61 saved results with the historical C46 oracle failure; realistic corpus 181/181 (retry oracle timeouts with a 60-second limit); two boundary probes exact; 6 passing unit files and 64 historical failures; 181 sanitized exact outputs. Oracle timeouts may vary with machine load. The realistic replay wrapper selects the explicitly Smart-only corpus contract; Classic is unchanged and intentionally absent from this new corpus.

next:
- Orchestrator review/merge, then native AE preview/ROI validation.
- Separate work for historical fixture/source-identity tests and original allocator/unavailable-oracle boundaries. No release gate, forbidden-action list, other plugin, MAIN, or emulator source changed; no push.
