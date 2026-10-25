status: blocked
summary:
- The source fix and synthetic oracle validation are complete; actual A02h AE suite values remain unavailable.
- Built and registered space-free F53/F54 float-colour workers; both pass 900/900 Smart cases (seeds 1–3, n100 per PF8/16/32).
- Both pass nine output-sensitive Key/Invert/Gamma qualification cases; zero mismatches or Mac-only refusals.
- Default seed1/n300 preserves all 300 prior result records; all 15 corpus replays match saved results.
- Synthetic A02h witness is exact. Do not claim literal reproduction of its uncaptured AE float values or native AE acceptance.

facts:

Original analysis and existing fix:
- `S02-evidence/original-colour-read.txt` retains exact decompiler excerpts and source SHA-256. The original Smart builder `0x180004e10` reads version, Enable Key, then (if enabled) Invert Key and Key Color disk ID2. The colour getter is `0x1800014a0 -> 0x180007540 -> 0x180016660`: parameter checkout, PF ColorParamSuite v1 floating-point call, error check, suite release, parameter check-in. `0x180001590` only reorders ARGB to RGBA; it does not quantize the float.
- After smoothing controls it reads Gamma mode/value, then, for Gamma Colors, count and disk IDs10 onward in ascending order. The separate byte getter `0x180016600` is not called by this render colour path. No float-vs-byte equality check occurs there.
- U01 records Key disk ID2/public slot2 and Gamma disk IDs10–14/public slots11–15, matching the worker fixture's slot mapping. P02f records the public Smart builder/geometry boundary.
- The first-run source change removes `DecodedColorsMatch` and reads only enabled Key/active Gamma colours through the suite. It changes no smoothing arithmetic. The first-run report is retained in `S02-evidence/first-run-report.md`.
- Audit `rg -n 'u.cd.value|GetFloatingPointColor' mac --glob '*.cpp'`: no other general float-must-equal-byte/255 guard found. Smoother v1 reads bytes; ColorKeep/ColorKey retain byte and float representations; historical fixed-fixture predicates in ColorKey/DistanceGradation are not this general guard. No other plugin changed.

Resume commands/results (all logs and reports under `S02-evidence/resume/`):
- `python3 tools/emulation/aexcompat_patches/build_S02.py --parent F53` and `--parent F54`: both exit 0, release builds 2m57s and 2m54s. Real source copies were under `~/Documents/Projects/Personal/04_Tools/AEXCompat-S02-build-F{53,54}`, target/tmp under `~/.cache/olm-emu/build-S02-F{53,54}`. All build trees were removed. Parent sources stayed read-only.
- Workers installed and registered in `~/.cache/olm-emu/INDEX.json`:
  - `worker-S02-F53/aex-guest-worker`: SHA-256 `3fc62ca294cc70f1a9a4b597f3154d7d1d2ceba016be4935751d7f0fcb5c4860`.
  - `worker-S02-F54/aex-guest-worker`: SHA-256 `3127791d33b4b1ffd34a263826262ff01ee6b5b26b8d23f43224817d6e1e2b61`.
  - Compressed build manifests bind parent callback, patched callback, recipe and source tree. The patch changes the host suite fixture only, not AEX algorithm code.
- `s02_float_campaign.py` on each worker, seeds 1,2,3, n100 **per depth**: 900/900 Smart exact per worker, zero mismatches/refusals, no first mismatch. All 900 full case result records are identical between workers. AEX SHA-256 remains `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
- Paired byte-only controls showed zero output-sensitive random cases: the small perturbations did not change these sampled outputs. This limitation is explicitly retained, not counted as independent delivery proof.
- `--qualify-only`: all nine cases per worker are exact AND change original output versus the byte control. Each depth tests Key, Invert Key and Gamma Colors. Key uses byte-white vs float near-black; Gamma uses byte-red (absent from the grey checker) vs float near-grey. An earlier Gamma control used white, which was also present and was insensitive (3/3); that failed sensitivity test is retained as `qualify-all-F53.json`. Replacing that control with absent red established the membership boundary without modifying production code.
- Every campaign checks that removing opt-in floats restores identical generated parameters/pixels/geometry for seed1's first 300 cases. Default sampler and existing corpus generation/replay are unchanged.
- Fresh default seed1/n300 against S02-F53: 300 Smart exact, zero pixel mismatches, 300 unchanged Classic refusals. All 300 complete `result` objects equal the earlier F46-backed default report, not just its counts.
- Corpus replay: top-level 8/8, P04c2 cropped-checkout 4/4, T15b odd/even 3/3; each report has `replay_matches_saved=true`. First T15b invocation omitted its recorded max-size623 and failed setup; second lacked the opt-in size flag and failed argument validation. Corrected invocation passes without editing any corpus.
- A02h witness: unchanged corpus pixels/parameters plus synthetic float-v1 suite values is Smart exact on both workers, output SHA-256 `47794b301c518d0c409b12fbe9909cf5b298a23a2893b35504d207b536106247`. Enable Key=0 and Gamma=None, so these colours are unused by the original. A02h explicitly says its disagreeing suite component was not captured. The actual float tuple is not present in the supplied evidence.

- `ref_vs_fast.py --small 100 --hd 0 --uhd 0 --parallel 1 --jobs 1`: exit0, 92 exact renders, eight identical refusals, zero mismatches. Separate `--small 0 --hd 3 --uhd 3`: exit0, 6/6 exact renders, all three depths at 1080p and 4K, zero refusals/mismatches. Build/result manifests retained.
- `git diff --check`: exit0. Regenerable native build/output trees removed; no owned background processes remain.

inference:
- The removed equality check was a Mac-only admission restriction. Output-sensitive Key and Gamma fixtures confirm that both source host and original worker consume independent float colours.
- The synthetic witness supports removal of the reported refusal, but it is not a capture/replay of AE's actual float tuple. That acceptance item remains blocked on a native callback-value capture; no native AE exactness is claimed.
- Finite campaigns establish these sampled boundaries only. The random perturbations alone do not prove sensitivity; the targeted qualification cases provide that evidence.

changed_files:
- Existing first-run changes: `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`, `cli/OLMSmoother2/shim/OLMSmoother2.h`, `tools/emulation/olmsmoother2_public_key_gamma_harness_20261001.cpp`, `tools/fuzz/adapters/{olmsmoother2,public}.py`, `tools/fuzz/{core,run}.py`.
- Resume: `tools/emulation/aexcompat_patches/build_S02.py` fixes physical source/build/temp paths and cleanup.
- Resume: `tools/fuzz/s02_float_campaign.py` provides stratified campaigns, byte controls, sampler invariance, synthetic witness and output-sensitive qualifications.
- This report and `orchestra/reports/S02-evidence/` preserve evidence, including unsuccessful setup/sensitivity attempts.

verify:
Run from this worktree (one process per command; workers already installed):
```sh
export TMPDIR="$PWD/orchestra/state/S02-smoother2-float-color-guard"
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "$TMPDIR"
for family in F53 F54; do
  python3 tools/fuzz/s02_float_campaign.py --worker "$HOME/.cache/olm-emu/worker-S02-$family/aex-guest-worker" --scratch "$TMPDIR/recheck-$family" > "$TMPDIR/recheck-$family.log" 2>&1
  python3 tools/fuzz/s02_float_campaign.py --qualify-only --worker "$HOME/.cache/olm-emu/worker-S02-$family/aex-guest-worker" --scratch "$TMPDIR/recheck-qualify-$family" > "$TMPDIR/recheck-qualify-$family.log" 2>&1
done
# Expected per family: 900 exact, first_failure=null; qualification 9 exact+sensitive, exit 0.
python3 tools/fuzz/run.py --plugin olmsmoother2 --worker "$HOME/.cache/olm-emu/worker-S02-F53/aex-guest-worker" --n 300 --seed 1 --jobs 1 --shrink-attempts 0 --scratch "$TMPDIR/recheck-default" --report "$TMPDIR/recheck-default.json" --corpus "$TMPDIR/recheck-corpus" > "$TMPDIR/recheck-default.log" 2>&1
# Expected: Smart exact300, mismatch0, Classic refusal300.
python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2 --jobs 1 --scratch "$TMPDIR/recheck-replay" --report "$TMPDIR/recheck-replay.json" > "$TMPDIR/recheck-replay.log" 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2/P04c2-cropped-checkout --jobs 1 --scratch "$TMPDIR/recheck-p04" --report "$TMPDIR/recheck-p04.json" > "$TMPDIR/recheck-p04.log" 2>&1
python3 tools/fuzz/run.py --plugin olmsmoother2 --replay tests/fuzz_corpus/olmsmoother2/T15b-odd-even-realistic --max-size 623 --size-sampler odd-even-v1 --jobs 1 --scratch "$TMPDIR/recheck-t15" --report "$TMPDIR/recheck-t15.json" > "$TMPDIR/recheck-t15.log" 2>&1
# Expected: replay_matches_saved=true for 8,4,3 cases respectively.
python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 --small 100 --hd 0 --uhd 0 --parallel 1 --jobs 1 --scratch "$TMPDIR/recheck-ref-fast" > "$TMPDIR/recheck-ref-fast.log" 2>&1
python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 --small 0 --hd 3 --uhd 3 --parallel 1 --jobs 1 --scratch "$TMPDIR/recheck-ref-fast-large" > "$TMPDIR/recheck-ref-fast-large.log" 2>&1
# Expected ref/fast: small exact92/refusal8/mismatch0; large exact6/refusal0/mismatch0.
git diff --check
```

next:
- Capture the actual `PF_GetFloatingPointColorFromColorDef` values and legacy bytes from A02h's native AE project using a coordinated instrumented host run. Supply those exact values to the now-qualified fake hosts and repeat the witness. Until then, literal AE-float reproduction remains blocked.
- Rebuild/retest the candidate in native AE as an orchestrator-coordinated follow-up; no installed bundle, MAIN, release gate or ledger was modified here. No push.
