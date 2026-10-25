status: done
summary:
- Threaded Smoother2's independent pixel stage with the shared GCD helper; unchanged arithmetic and ordered diagnostics.
- Default full-frame render is approximately 3x faster; reference/fast hashes match at caps 1, 2 and 8.
- 850 generated AEX cases: 701 Smart exact, 149 matched refusals, zero pixel mismatches and zero Smart Mac-only refusals; 15/15 corpora replay true.
- 50 forced-cap cases, 50 TSan fuzz cases, and same-process four-render checks pass.
- Existing unit failures are unchanged: 100 tests, 17 failures and 7 errors both before and after.

facts:

All numbers below are measured. No release-gate or ledger files, oracle sources, or other plugin sources were changed. No oracle was rebuilt. Scratch remained below 5 GiB; observed memory-pressure free values were 51–61%.

Profile and implementation:
- `lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07b-evidence/profile.py`: sample exit 0 and host exit 0. The 4K PF32 sampling window points to `win_FUN_18000cce0_orchestrate`; 619 of 756 main-thread samples sit at its RenderBits call site. This is a sampled window, not a full-frame time fraction. There is no SubHandler8Memory hotspot in this Smoother2 profile.
- Only the pixel stage is parallelized. Its input/class planes are complete and immutable; each task writes disjoint output rows. Polygon traversal, reductions, LUT evaluation and packing are unchanged. The output-plane argument to the orchestrator is unused.
- `OLM_REFERENCE_BUILD` always selects the helper's sequential path. `OLM_PARALLEL_MAX=1/2/8` caps tasks in fast builds. Frames below 65,536 pixels and ordered histogram/writer/trace diagnostics remain sequential; minimum grain is eight rows.
- `g_olmsmoother2_current_switch_idx` previously had unconditional per-pixel writes; `g_olmsmoother2_force_input_premultiply` had unconditional per-render writes. Both are now thread-local. Other diagnostic settings remain the existing CLI-only configuration, which must not be mutated concurrently with rendering.

Correctness:
- `campaigns.py` ran default seed 1 n300; realistic-v1 and realistic-v2 seeds 1 and 20261025 n100 each; odd-even-v1 seed 2026 n150 with T15b's realistic-v1 geometry and width/height ceiling 623. All six exit 0. Smart counts are respectively 300/0, 61/39, 59/41, 100/0, 100/0, 81/69 (exact/matched refusal). Every refusal has an AEX rejection in the same case. Classic remains the documented unowned/refusing route; it is not the contract route.
- `replay.py`: standard `tools/fuzz/run.py --replay` with saved workers and matching size flags, 12/12 at max-size 256 and 3/3 at max-size 623; `replay_matches_saved=true` for both. The first all-in-one attempt failed setup because mixed corpora require different `--max-size`; no corpus was changed.
- `ref_vs_fast.py`: heavy preset, 20 small + 3 HD + 3 UHD cases, caps 1/2/8: 72 exact comparisons, 6 identical refusals, 0 mismatches. Defaults, 3 HD + 3 UHD, all depths and caps: 18 exact comparisons, 0 refusals/mismatches. Every `first_mismatch` is null. Full output/source hashes are in `diff*-results.jsonl` and `diff*-builds.json`.
- P00b's heavy corpus03 and corpus05 contain identical parameter lists (canonical JSON SHA-256 `d5ca25656b0921c55cc0598323af97f763888033eb704e65fdb8ba794eab7732`); corpus03 represents both in the driver registry. Both named P00b cases were measured.
- `threads.py`: all 50 generated cases match hashes at caps 1/2/8; all 50 TSan cases match those hashes and exit successfully with `TSAN_OPTIONS=halt_on_error=1`. Half the cases are tiled to 257x259 to cross the threading threshold. Example case 0 output SHA-256: `01eb64c1eac63feeb68833b65ca8669b2c0c77945cb6dd9bbc18326fd233c98b`.
- `unit_comparison.py`: individually isolated unittest modules avoid the initial discovery collision. With SDK links present, both the pinned pre-ticket source and candidate run 100 tests: 76 pass, 17 failures, 7 errors. All named failures/errors and all 20 module exit codes match. Existing failures include missing retained files, identity/hash assertions, and a pre-existing cross-plugin assertion; they were not patched. Full logs are retained.

Timing (seconds per render):

Every P00b, sample, threshold and concurrency timing run held `lockf -k ~/.cache/olm-emu/bench.lock`. The table uses the pre-change registered P00b bundle and the new candidate under the same P00b host. Both batches returned success for all 18 rows.

| Params | bpc | Before 1080p | After 1080p | Before 4K | After 4K |
|---|---:|---:|---:|---:|---:|
| default | 8 | 0.386081 | 0.129975 | 1.545122 | 0.487191 |
| default | 16 | 0.383423 | 0.124382 | 1.583209 | 0.503390 |
| default | 32 | 0.391669 | 0.125430 | 1.587700 | 0.482612 |
| corpus03 | 8 | 0.374042 | 0.125835 | 1.488966 | 0.508911 |
| corpus03 | 16 | 0.379047 | 0.137466 | 1.522514 | 0.493360 |
| corpus03 | 32 | 0.385351 | 0.133729 | 1.507480 | 0.503775 |
| corpus05 | 8 | 0.377855 | 0.124823 | 1.529194 | 0.517366 |
| corpus05 | 16 | 0.387373 | 0.132931 | 1.550853 | 0.545242 |
| corpus05 | 32 | 0.390486 | 0.146016 | 1.582192 | 0.528962 |

A fresh Universal `OLM_REFERENCE_BUILD` bundle was also measured under the same lock. Against that sequential build, speedups span 2.65–3.20x across the 18 cells. Raw reference, initial baseline and after rows/manifests are retained separately. This is one sample per P00b cell; shared-machine load can still affect results despite the benchmark lock.

Threshold and concurrent frames:
- A test-only copied-source variant removes the size gate to measure small-frame overhead without changing arithmetic. At 16x16, cap 1 vs 8 single-render times were about 0.018 vs 0.020 ms, and four-render times about 0.020 vs 0.025 ms. At 32x32, single-frame improved but four-frame time slightly worsened. The production threshold is conservatively 256x256 (65,536 pixels).
- An initial 256x256 run was load-affected: cap-8 four-render time 5.768 ms vs cap-1 4.727 ms; an independent same-code run measured 3.700 vs 4.857 ms. This discrepancy was retained, not discarded. A locked five-repeat recheck alternated cap order.
- Recheck medians for 256x256 single / four simultaneous renders: cap 1 **4.592 / 5.344 ms**, cap 2 **3.330 / 4.422 ms**, cap 8 **2.636 / 4.320 ms**.
- Recheck medians for 1080p single / four simultaneous renders: cap 1 **200.760 / 240.566 ms**, cap 2 **130.743 / 181.688 ms**, cap 8 **92.396 / 160.013 ms**. Four simultaneous frames therefore improve about 1.50x at 1080p, without deadlock or median slowdown. This harness uses a fixed typed pattern and generated parameters, so its absolute times are not the P00b matrix times.
- The four renders share one process and call the production RenderBits with independent worlds and immutable parameters. All outputs match across caps, repetitions and threshold variants. A same-process TSan run at 257x259 also passes all three caps without reports. This tests render-core concurrency, not native AE scheduling.

Builds and reproducibility:
- Universal arm64/x86_64 candidate and reference builds succeed with one build job. Initial build failed for absent SDK links; `scripts/setup_ae_sdk_links.sh` resolved it.
- Durable bundles and P00b host copies are registered in `~/.cache/olm-emu/INDEX.json` under `P07b-smoother2` and `P07b-smoother2-before`. Candidate Mach-O SHA-256: `65f267b8312468a776479d7ff3ed31159a2994495776ec454d474a4be4abf2d5`; reference: `9cf3726e774e7679c7be33ae67eee3cbf47f5f37dc1ceebbac50b7657765b6f2`. They are validation artifacts, not newly installed AE plugins or AEX oracles.
- Regenerable scratch binaries/build trees were removed after validation; logs and committed evidence remain.

inference:
- Independent pixel tasks remove the measured serial bottleneck while retaining each pixel's original computation order. The hashes support exactness within the tested cases, not universal proof over all inputs.
- The conservative small-frame threshold avoids measured tiny-frame overhead. No floating-point reduction was parallelized or reassociated.
- Native AE preview gains should follow the single-frame speedup, but native AE interactive timing was not measured. The existing red unit suite remains a separate maintenance issue.

changed_files:
- `mac/OLMSmoother2/Mac/OLMSmoother2_port.cpp`: shared-helper row dispatch and two thread-local diagnostic variables.
- `tools/perf/ref_vs_fast.py`: Smoother2 registry/heavy preset, task-cap defaults, and explicit default-parameter large-frame mode.
- `orchestra/reports/P07b-evidence/*`: reproducible scripts, validation results, logs and build provenance.
- `orchestra/reports/P07b-smoother2-threading.md`.

verify:

Quick, read-only evidence/source validation:
```sh
python3 orchestra/reports/P07b-evidence/verify.py
git diff --check
```
Expected: `P07b evidence OK`, 850 AEX cases, 15 replays, 96 reference/fast comparisons, 50 forced-cap + 50 TSan cases, unchanged unit failures, matching concurrent hashes and faster cap-8 medians.

Full rerun (run sequentially; scripts place scratch inside this ticket):
```sh
scripts/setup_ae_sdk_links.sh
python3 orchestra/reports/P07b-evidence/campaigns.py
python3 orchestra/reports/P07b-evidence/replay.py
python3 orchestra/reports/P07b-evidence/threads.py
python3 orchestra/reports/P07b-evidence/unit_comparison.py
python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 --small 20 --hd 3 --uhd 3 --parallel 1 2 8 --jobs 1 --scratch orchestra/state/P07b-smoother2-threading/diff
python3 tools/perf/ref_vs_fast.py --plugin olmsmoother2 --small 0 --hd 3 --uhd 3 --no-large-corpus --default-params --parallel 1 2 8 --jobs 1 --scratch orchestra/state/P07b-smoother2-threading/diff-default
python3 orchestra/reports/P07b-evidence/build.py
python3 orchestra/reports/P07b-evidence/build.py --reference
lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07b-evidence/benchmarks.py
lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07b-evidence/recheck_concurrency.py
```
Expected correctness counts above; timing values vary with load. `unit_comparison.py` temporarily restores the pinned pre-ticket source and then restores the candidate in `finally`; do not run concurrent source builds during it. The concurrency scripts require the host generated by `threads.py`.

next:
- Orchestrator review/merge. No remaining implementation work for this ticket.
- Optional follow-up: repair baseline fixture/identity unit failures and measure native AE preview/multi-frame behavior without changing the release gate in this ticket.
