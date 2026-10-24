status: blocked
summary:
- Heavy corpus09 Mac renders improved from 17.75–18.32 s to 1.38–1.43 s at 1080p; 4K improved from three >60 s timeouts to 5.70–5.92 s.
- Added plugin-local IEEE/SSE fast paths, channel SIMD, eight independent row partitions, and strict `-O2` rotation compilation; no approximation or accumulation reorder.
- Acceptance is blocked by one inherited Smart mismatch in fresh realistic-v1 seed 2053, case 9: parent and optimized outputs are identical. Final campaigns: 994 exact / 1,000, one mismatch, five original timeouts, zero Mac-only refusals.
- Built Universal bundle: 100/100 Smart exact. Six heavy witnesses are Smart exact; the inherited mismatch is also retained. All 298 corpus cases replay true on both routes.
- Unit file results unchanged: 9 pass / 30 fail before and after. Existing failures and noncontract Classic mismatches are not promoted to conformance.

facts:
- Parent source: `9123f22a0cee8a7592ca7a89ec4f0a962d02b9a8`, branch `orch/P05a-directionalblur-performance`. M1 Pro, 16 GiB. Observed memory free: 60–62% during final verification (61% initially). Scratch stayed below 20 MiB during observed checks.
- `python3 tools/fuzz/build_F47_bundles.py --plugins OLMDirectionalBlur --scratch orchestra/state/P05a-directionalblur-performance/before` built the untouched baseline. `python3 orchestra/reports/P05a-evidence/measure.py --label final2 --build` built the final Universal arm64/x86_64 bundle and invoked the unchanged P00b driver with `--phase matrix --cases default corpus09 --situations full 4k --jobs 1 --timeout 60`.
- Baseline bundle SHA256: `9a12b3c0e4886afc769c8ce8db6aaaf797dde0da72757cdf859f56b82551ef84`; final: `0eda8c52b02c6f44493be2afde66889b6d1763431fea54f59696d3cf5309b016`. These are **Mac SDK-host timings**, not timings of the original AEX or native After Effects. Each cell is one render on the shared machine; no statistical speedup claim.

| Preset | Depth | Before 1080p s | Final 1080p s | Before 4K s | Final 4K s |
|---|---:|---:|---:|---:|---:|
| default | 8 | 0.002879 | 0.002950 | 0.013872 | 0.011262 |
| default | 16 | 0.005852 | 0.003455 | 0.022681 | 0.015994 |
| default | 32 | 0.010503 | 0.006444 | 0.042645 | 0.028483 |
| corpus09 | 8 | 17.751039 | 1.378254 | >60 timeout | 5.701336 |
| corpus09 | 16 | 18.231521 | 1.425048 | >60 timeout | 5.747444 |
| corpus09 | 32 | 18.323172 | 1.391768 | >60 timeout | 5.915160 |

- Intermediate measurements are retained, not substituted for final results: scalar fast paths / optimized rotation alone gave 15.72–15.91 s at 1080p; four-partition SIMD gave about 2.9 s; eight partitions with volatile intermediates gave 1.95–2.07 s / 8.34–8.74 s. Removing forced scalar stack spills under the existing strict floating-point flags produced the final table. `*-matrix.jsonl` and manifests retain exact measurements and parameter identities.
- `sample PID 2 1 -file ...` succeeded before and after. Before: 1,548 terminal scatter samples. Final: 3,219 terminal scatter samples and 1,025 rotation samples, with seven dispatch worker threads plus the caller visible. Counts span different thread populations and are **not** comparable percentages. The separately profiled final 4K PF32 render completed in 6.347597 s. See `before.sample.txt`, `final.sample.txt`, and `profile.json`.
- `float_witness.cpp`, compiled with `-O2 -fno-fast-math -ffp-contract=off`: **16,001,296** old/new scalar arithmetic bit comparisons, zero mismatches. Explicit boundaries include both zeros, subnormals, finite extrema, infinities, quiet/signaling NaNs, signs and payloads, plus four million random operand pairs.
- `python3 orchestra/reports/P05a-evidence/kernels.py`: **10,000 scatter**, **120 rowdriver**, and **200 rotation** array comparisons, zero mismatches. Old kernels are extracted from the parent commit; old rotation is compiled at its original `-O0`, old rowdriver at `-O2`, and new kernels at `-O2`. Arbitrary float bits exercise exceptional values and bounded RGB with exceptional accumulators; 65–67 rows cross the parallel threshold and uneven partitions. Destination, denominator, and alpha arrays are compared bit-for-bit. There is no first mismatch in these comparisons.
- `python3 orchestra/reports/P05a-evidence/witness.py`: six heavy-preset inputs at 17×11 / 32×24, all depths, including high PF16 and finite PF32 signed-zero/subnormal/HDR samples. Original AEX Smart output equals candidate bytes in all six. Classic has six retained mismatches. New corpus: `tests/fuzz_corpus/olmdirectionalblur/P05a-performance/`.
- `python3 orchestra/reports/P05a-evidence/acceptance.py`: final source campaigns below; standard CLI, one job, no shrinking. F46/F52c/F53 retained workers were used by absolute path and never rebuilt. Command vectors, worker/AEX hashes, output hashes, full outcomes and source bindings are retained in `P05a-evidence/`.

| Sampler | Seed | n | Smart exact | Smart mismatches | Mac-only refusals | Original unavailable |
|---|---:|---:|---:|---:|---:|---:|
| default | 1 | 300 | 298 | 0 | 0 | 2 |
| realistic-v1 | 1 | 100 | 100 | 0 | 0 | 0 |
| realistic-v1 | 2053 | 100 | 99 | 1 | 0 | 0 |
| realistic-v2 | 1 | 100 | 100 | 0 | 0 | 0 |
| realistic-v2 | 2053 | 100 | 100 | 0 | 0 | 0 |
| odd-even-v1 + realistic-v1 | 2026 | 150 | 150 | 0 | 0 | 0 |
| odd-even-v1 + realistic-v1 | 2027 | 150 | 147 | 0 | 0 | 3 |

- The default campaign has zero exact-to-non-exact changes versus the P04b2 baseline. Original unavailable cases remain default seed 1 indices 274/289 and odd-even seed 2027 indices 5/50/54; these are transport time budgets, not evidence of original PF_Err refusal or pixel equality. No refusal predicate or budget was changed.
- **Blocking boundary:** realistic-v1 seed 2053 index 9, PF32 signed input, input 7×5 / full layer 19×15, downsample 1/3, request `[6,1,7,3]`. Six of eight float words differ (24 bytes); first expected word bytes `2ba6b6bd`, actual `8c9cd9be`. Original output SHA256 `cad415cde5b57805cf2cccfc4a01282c0105868619f51016984a6d7b8d015ed2`; parent and final output both `526ce74f6cb8e1bbfe6ec36c9c7a524557f423ef943a85573c2151d9bd99ef60`.
- `python3 orchestra/reports/P05a-evidence/check_boundary.py` rebuilt the parent rowdriver/rotation alongside unchanged production code and evaluated the same regenerated input against F52c. All three parent repeats and all three final repeats returned those same hashes and mismatch. Thus this is not an optimization-induced output change. The retained case is `P05a-performance/preexisting-realistic-v1-seed2053-case9.json`; `boundary-check.json` preserves all six comparisons. The standard campaign CLI exits 0 even when it records this mismatch; the explicit summary assertion caught it. Earlier commentary based on CLI success was corrected after inspecting case outcomes.
- The actual final Universal bundle, using `run.py --candidate plugin-bundle --geometry realistic-v2 --seed 2053 --n 100`, is 100/100 Smart exact, zero mismatches/refusals (`bundle-realistic-v2-2053.json`).
- All 298 standard corpus replays match their saved outcomes: 83 root, 200 P02j, four T15b, four P04b2, seven P05a; both routes, with the recorded max-size and odd-even sampler flags. No existing corpus expectation changed. Replay true includes the explicitly retained inherited mismatch; it is not a zero-mismatch claim.
- `OLM_TEST_JOBS=1 python3 orchestra/reports/P05a-evidence/unit_tests.py --label before` and `--label after`: 39 files each, 9 pass / 30 fail, zero per-file exit changes. Historical source-hash assertions and test dependency/build failures remain visible in the committed diagnostic tails. The untouched-source baseline was rerun after an initial mixed-source unit launch was discarded. Scheduling deviation: an early build was launched while benchmark and unit drivers were active; subsequent final verification used at most two task-owned runs, with one job per build/emulator driver.
- No MAIN, oracle source, release gate, ledger, shared float helper, or other plugin source was modified. No push or history rewrite. Disposable build trees and task-owned child processes were removed after verification; reproducible scripts and logs remain. `git diff --check` passed.

inference:
- A non-NaN IEEE result cannot have a NaN operand, so scalar SSE payload inspection is redundant there. Every NaN result still receives the existing operand-aware SSE correction.
- SIMD lanes represent independent channels plus the denominator, never successive contributions. For finite contribution and absolute RGB ≤1, products remain finite; an addition can only propagate an accumulator NaN, with a single NaN operand. General exceptional products/sums use the exact lane-wise SSE fallback. MAXSS selection retains its original scalar comparison.
- Scatter and prepass clip all accesses/writes to their own row. Partitioning rows therefore preserves each pixel's complete contribution sequence and requires no shared reduction. The public caller remains synchronous through `dispatch_apply_f`.
- On the supported ARM64/x86_64 targets, explicit float operations with fast-math and contraction disabled preserve binary32 rounding without volatile stack traffic. Rotation inlining and `-O2` use the same strict flags as the already established source fuzz harness.
- Kernel equivalence and matching parent/final boundary hashes support preservation of the existing arithmetic behavior. The requested zero-mismatch acceptance condition is nevertheless not met: the fresh seed exposed a pre-existing cropped/downsampled Smart boundary. No geometry correction was attempted within this performance-only ticket. The five unavailable originals, historical unit failures, Classic behavior and broader native-AE release scope also remain unclosed.

changed_files:
- `core/dblur_float.h` (DirectionalBlur-only scalar/vector SSE helpers)
- `core/dblur_rowdriver.cpp` (channel SIMD, bounded arithmetic, independent row partitions, redundant spill removal)
- `core/dblur_rotate.cpp` (inline arithmetic wrappers using plugin-local helpers)
- `mac/OLMDirectionalBlur/Mac/OLMDirectionalBlur.xcodeproj/project.pbxproj` (strict `-O2` rotation)
- `tests/fuzz_corpus/olmdirectionalblur/P05a-performance/` (six heavy witnesses and one explicitly labelled inherited mismatch)
- `orchestra/reports/P05a-evidence/` (reproduction scripts and measured evidence)
- `orchestra/reports/P05a-directionalblur-performance.md`

verify:
Run sequentially from this worktree (the following rebuilds only the candidate and local test kernels, never the oracle):
```sh
export OLM_TEST_JOBS=1 PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/orchestra/state/P05a-directionalblur-performance"
export TMP="$TMPDIR" TEMP="$TMPDIR"
mkdir -p "$TMPDIR"
clang++ -std=c++17 -O2 -fno-fast-math -ffp-contract=off -I. orchestra/reports/P05a-evidence/float_witness.cpp -o "$TMPDIR/float-witness"
"$TMPDIR/float-witness"
python3 orchestra/reports/P05a-evidence/kernels.py
python3 orchestra/reports/P05a-evidence/measure.py --label final2 --build
python3 orchestra/reports/P05a-evidence/profile.py
python3 orchestra/reports/P05a-evidence/witness.py
python3 orchestra/reports/P05a-evidence/check_boundary.py
python3 orchestra/reports/P05a-evidence/unit_tests.py --label verify
python3 orchestra/reports/P05a-evidence/acceptance.py
python3 tools/fuzz/run.py --plugin olmdirectionalblur --candidate plugin-bundle --plugin-bundle orchestra/state/P05a-directionalblur-performance/final2/xcode/OLMDirectionalBlur/products/OLMDirectionalBlur.plugin --geometry realistic-v2 --seed 2053 --n 100 --jobs 1 --budget-minutes 30 --shrink-attempts 0 --scratch orchestra/state/P05a-directionalblur-performance/bundle-fuzz --corpus orchestra/state/P05a-directionalblur-performance/bundle-failures --report orchestra/reports/P05a-evidence/bundle-realistic-v2-2053.json
python3 orchestra/reports/P05a-evidence/summarize.py
git diff --check
```
Expected: zero arithmetic/kernel mismatches; heavy renders approximately <2 s / <8 s on an otherwise comparable M1 Pro; six Smart exact witnesses; 9/39 unit file passes; the campaign table above **including one inherited Smart mismatch** (original timeouts may vary with load); six identical parent/final boundary mismatch hashes; 100 bundle Smart exact; all 298 replay outcomes true. The summary explicitly reports blocked acceptance. `acceptance.py --replay-only` runs only standard corpus replay. Profiling affects timings and is a separate render.

next:
- Follow-up ticket: fix the inherited realistic-v1 cropped/downsampled Smart boundary, using the retained seed 2053 case 9 and F52c original as the witness. Do not substitute another fresh seed to hide this failure. This blocks acceptance of P05a as fully done, although the measured performance goal is met.
- Preserve separate follow-ups for the five inherited original execution/time-budget cases, historical unit fixture/dependency repairs, and noncontract Classic conformance. No pixel tuning against missing original outputs.
