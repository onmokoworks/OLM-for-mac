status: partial

summary:
- Two clusters committed: blurred Smart composition and unblurred PF8 normalization/staging.
- Seed 1 Smart exact improves 225 -> 235 -> 239; fresh seed 3 improves 217 -> 227 -> 230. Every base-exact byte is preserved.
- Independent blurred matrix 432/432 and PF8 field matrix 216/216 are exact; campaign/matrix/corpus ASan+UBSan agree.
- Two corpus entries improve mismatch->exact; final replay is 145/145 saved matches and 145 actual Smart exact.
- PF32 admission investigation continues; broad gate removal remains rejected.

facts:
- Starting HEAD `b4350d648947640ebdc3459c5e0451cbef54c64f`, branch `orch/C08-dg-smart-r2`. Read AGENT_GUIDE, GOTCHAS, DistanceGradation ledger restrictions, compatibility plan, T07/F01/F02/C03 and F10/F12 method. MAIN and emulator sources remain read-only; no worker rebuild.
- Original AEX SHA-256 `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`; retained worker SHA-256 `3cb4855b7b3fb235388391cca11ddd1aa70fb6b2d4e34737a3e368d621184261`, absolute path `/Users/onmk/Documents/Codex/2026-10-05/task-3/AEXCompat-containment/guest/target/release/aex-guest-worker`. Cache INDEX inspected, no substitution. Typed original-AEX CPU Smart is the oracle; no native AE/UCRT claim.
- `run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0` with ticket scratch corpus exits 0: Smart 225 exact / 17 mismatch / 51 refusal / 7 uncompared. AEX Smart 290 success / 8 reject / 2 budget. Classic 10 exact / 290 mismatch.
- Current-base all-gates-off ASan/UBSan experiment, `probe_distancegradation_smart_C03.py --experiment all --sanitized --smart-only` with seed 1, n300, jobs2, timeout30: 258 exact / 32 mismatch / 10 uncompared, no sanitizer diagnostic/candidate failure. Original AEX 290 success / 10 reject. Among previously refused: HDR 12 exact; signed 10 exact / 1 mismatch / 1 uncompared; nonfinite 1 exact / 7 mismatch; SDR 10 exact / 7 mismatch / 2 uncompared. This refutes broad admission; it is diagnostic only.
- Six natural PF8 public Smart captures (RGB/Layer × Inside/Outside/Both, Box size 1) preserve original builder state, source and staged field. Relocated callbacks reproduce every public output hash. Source normalization and distance scalar match Mac before the change. Inside field bytes are `2a2a2a0080808080d4d4d4ff`. AEX first unowned output is `002a2a00`, before Mac RGB is `002ad500` and Layer `004080c0`. First divergent stage: callback ownership/color selection; G byte 2 for RGB, R byte 1 for Layer. All six full outputs are exact after the change.
- Static `181172906..18117291b` merges blurred planes with the pre-blur scalar; PF8 callback `18117098f..1811709c3` loads its independent field RGB lanes, and `181170a7d..181170a88` branches before interpolation at FLOAT32 0.0001. Layer selection `181170be9..181170bf1` uses original source RGB. PF32 sibling `181170f79..181170f92` has the same selection. Mac now retains/typed-stages the pre-blur scalar and uses it for the early-exit blue lane, extends early ownership and direct Layer selection to blurred Smart, and prevents Classic PF16 color inheritance/PF32 Both bypass from affecting Smart.
- `verify_distancegradation_smart_C08.py` runs ordinary before/current and current ASan+UBSan on 600 campaign inputs, 432 independent matrix inputs, and 145 corpus inputs. No diagnostic, timeout or byte/status disagreement. All base-exact outputs remain byte-identical. Fresh seed 3 census originally had one Mac timeout at 10 seconds; the verifier's 30-second limit completes it. Its AEX completion set is 289 success / 8 reject / 3 budget.

| Cluster 1 source | Seed 1 Smart exact | Fresh seed 3 Smart exact |
| --- | ---: | ---: |
| Before | 225 | 217 |
| After | 235 | 227 |

- Seed 1 now has 7 mismatches / 51 refusals / 7 uncompared using the same original references. Ten newly exact cases: 39,48,62,77,133,167,173,174,186,222. Three positive-blur cases remain nonexact (45,200,214); their field/blur cause is not declared closed.
- Independent matrix: 196 previous exact unchanged, 236 mismatch->exact, 432/432 final exact. PF8/PF16/PF32, 7×1/1×7, Box/Gaussian size1, Constant/Linear/Sphere, Inside/Outside/Both, RGB/Layer, background off/on, nontrivial colors and 3/5-byte padding.
- Corpus rebaseline table: all 145 unchanged (143 exact, two retained mismatches); no expectation edits. Production replay exits 0, all 145 match saved results.
- Existing beta tests: 9 pass; transactional tests: 2 pass. `git diff --check` passes. Evidence with hashes and full per-case comparisons: `reports/fuzz/olmdistancegradation_C08_blurred.json`. Cosmetic comment/brace cleanup after the first verifier build does not change arithmetic; the follow-on census binds final source.

Cluster 2 (base `d3fe5c3e`, PF8 direct-range normalization):
- Original helper `18117490b` selects the 255 normalization maximum, `181174942` calls cvNormalize, then owner `181172932` converts the merged world. The paired trace calls original public Smart without guest detours and binds both scaled planes and final public raw hashes.
- Saved case58 (1×70): first different scaled field word at y=53, AEX little-endian `00805443` (212.5), Mac `01805443` (212.50001525878906). Two scaled words differ. Case236 (1×40): the same first word at y=38; one word differs. AEX thresholded distance at those points is 5 with maximum 6. The new Mac scaled plane equals every original float word (70/70 and 40/40), before unchanged nearest-even byte packing. Final Smart outputs equal AEX hashes.
- General fix: distance helper accepts its normalization range maximum, default 1 to preserve every existing caller. Unblurred Smart PF8 requests 255 directly, then packs nearest-even and converts the byte to the callback's normalized scalar. Monotonic packing commutes with the Both maximum. Classic, PF16 reciprocal normalization/roundtrip, and positive-blur field arithmetic retain their prior contracts. No output-byte correction or special coordinate/value case is used.
- `verify_distancegradation_smart_C08.py --before-ref d3fe5c3e` replays 600 campaign inputs, 216 independent field inputs, and 145 retained corpus inputs through before/current/sanitized current. Seed1 235->239 exact; seed3 227->230 exact. No base-exact changes or sanitizer/ordinary disagreement. Seed1 remaining E/M/R/U: 239/3/51/7 on the recorded oracle set.
- Matrix: 194 previous exact preserved, 22 mismatch->exact, 216/216 final exact. 17×1 runs and 13×7 islands, thresholds3/6/13, Inside/Outside/Both, invert off/on, Constant/Linear/Sphere, RGB with background and Layer without, odd strides. Captured source/field semantics and the independent matrix are evidence for this unblurred PF8 operation only.
- Corpus update changes only result/provenance in the two rows below; input/control/reduction data, original oracle hashes, and Classic results are unchanged. Other 143 cases are unchanged exact. Production replay exits 0: `replay_matches_saved=true`, 145 completed; all 145 actual Smart outputs exact.

| Corpus case | Before Smart hash/status | After/AEX Smart hash/status |
| --- | --- | --- |
| `seed1_case000058_92552f06afe6.json` | mismatch `5832287e608ff319a3d2d04808d8693479d1d65d94c127060db4f770f50c41d7` | exact `76e3b8146375dd2ae3ad6b75971ea687c3cfef82a2da89ae1767bf8d27446806` |
| `seed1_case000236_92552f06afe6.json` | mismatch `49ca803bc1bbf1d905affbf79da3572dfb50d23756fa646ec133168b62cec4d3` | exact `5d89d966579f74a853f35e1f0c81b8f4f444ffbd4e65a6edb50581e912deb498` |

- Existing beta9 + transactional2 tests pass again; diff check passes. Two initial diagnostic builds exposed a missed debug-call/forward-declaration update; those compile defects were corrected before any rendering measurements. Evidence: `reports/fuzz/olmdistancegradation_C08_field.json`.

inference:
- The PF8 residual comes from normalizing to 1 and then scaling, which adds a floating-point rounding absent from the original direct-to-255 operation. The new paired pre-packing values distinguish this from a writer tie-rule error.
- The blurred callback residual inherited Classic heuristics and omitted the original early exit's distinct blue field lane. The measured operation is restored; this does not establish general blur/kernel equivalence.
- Broad PF32 refusal removal is unsafe. Finite-domain and inactive-filter subrules need independent boundary evidence; successful sampled HDR outputs alone do not authorize admission.

changed_files:
- `mac/OLMDistanceGradation/OLMDistanceGradation.cpp`
- `core/olmdistancegradation_fieldgen.{h,cpp}`
- `tools/emulation/trace_distancegradation_field_C08.py`
- The two corpus files in the table above
- `reports/fuzz/olmdistancegradation_C08_field.json`
- `tools/emulation/trace_distancegradation_smart_C08.py`
- `tools/fuzz/verify_distancegradation_smart_C08.py`
- `reports/fuzz/olmdistancegradation_C08_blurred.json`
- `orchestra/reports/C08-dg-smart-r2.md`

verify:
```sh
s="$PWD/orchestra/state/C08-dg-smart-r2"
mkdir -p "$s"
export TMPDIR="$s" TMP="$s" TEMP="$s" PYTHONDONTWRITEBYTECODE=1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 2 --shrink-attempts 0 --scratch "$s" --report "$s/verify-seed1.json" --corpus "$s/verify-corpus" > "$s/verify-seed1.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 3 --jobs 2 --shrink-attempts 0 --case-timeout 30 --scratch "$s" --report "$s/verify-seed3.json" --corpus "$s/verify3-corpus" > "$s/verify-seed3.log" 2>&1
python3 tools/fuzz/verify_distancegradation_smart_C08.py --scratch "$s/verify-blurred" --report "$s/verify-blurred.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed3.json" --blur-matrix --corpus > "$s/verify-blurred.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_smart_C08.py --blur-mode 2 --blur-size 1 --scratch "$s/verify-trace" --report "$s/verify-trace.json" > "$s/verify-trace.log" 2>&1
python3 tools/fuzz/run.py --plugin olmdistancegradation --replay tests/fuzz_corpus/olmdistancegradation --jobs 2 --scratch "$s" --report "$s/verify-replay.json" > "$s/verify-replay.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_*beta_20260820.py' > "$s/verify-beta.log" 2>&1
python3 -m unittest discover -s tests -p 'test_olmdistancegradation_smart_transactional_20260822.py' > "$s/verify-transactional.log" 2>&1
git diff --check
```
Expected at cluster 1: seed1 235/7/51/7, seed3 227 exact on the recorded oracle completion set; 432/432 matrix exact, every base-exact byte preserved, sanitizer equality throughout, six exact traces, 145/145 replay, 9+2 tests. Oracle timeout/reject labels can vary with time limit and shared-machine load; compare explicit successful-reference sets.

Additional cluster-2 verification (after generating the same seed campaigns above):
```sh
python3 tools/fuzz/verify_distancegradation_smart_C08.py --before-ref d3fe5c3e --scratch "$s/verify-field" --report "$s/verify-field.json" --campaign "$s/verify-seed1.json" --campaign "$s/verify-seed3.json" --field-matrix --corpus > "$s/verify-field.log" 2>&1
'/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' tools/emulation/trace_distancegradation_field_C08.py --scratch "$s/verify-field-trace" --report "$s/verify-field-trace.json" > "$s/verify-field-trace.log" 2>&1
```
Expected at cluster2: seed1 239/3/51/7; seed3 230 exact on the recorded reference set; 216/216 field matrix; both scaled planes and final outputs exact; no exact regression/sanitizer difference; 145/145 saved corpus matches.

next:
- Continue C08: test the narrow PF32 zero-size Box/Gaussian/Median admission rule; retain Mode5 and unsupported source domains.
- Three positive-blur mismatches, 51 refusals and native host/dependency boundaries remain. No release gate, ledger, other plugin, MAIN, worker or installed bundle changed. No push/history rewrite/stash; regenerable builds auto-clean, scratch below 5 GiB.
