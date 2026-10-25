status: blocked
summary:
- Prototyped independent classifier precomputation with ordered, sequential contour dispatch/fill.
- Initial 32-row prototype improves single-frame timings and passes native/oracle comparisons.
- Both 32-row and 128-row batching regress four-frame PF8 throughput; the no-slowdown condition is unmet.
- Stopped after these two batching hypotheses; restored all production sources and the performance driver.
- Experimental patches, scripts, compact evidence, and a registered initial bundle are retained for review only.

facts:

Base: `3d270436`, branch `orch/P07c-smoother-threading`. No production change is included in this commit. Neither release gates, ledger, MAIN, nor the original oracle were changed. `core/olm_parallel.h` already existed and was used unchanged by the prototypes.

Implementation/coverage identities:
- `P07c-evidence/candidate-initial.patch`: 32-row bands, four rows per GCD task, 65,536-pixel minimum. Native comparison, Universal bundle, and single-frame timing use this version. Exact source SHA-256: `f3c957da520368213d511993daaf18afa434ec164ade93716d198961fb7e402b` (asserted against the native build manifest).
- `candidate-band32.patch`: additionally makes `OLM_PARALLEL_MAX=1` execute the original interleaved scan and includes Smoother in the driver's default 1/2/8 list. Oracle campaigns, corpus replay, 50-case TSan, and repeated concurrency comparisons use this version. Default cap 8 computation is unchanged from the initial prototype.
- `candidate-band128.patch`: changes band/grain to 128/16. Only the concurrency/threshold probe was run for this version; do not transfer the other variant's coverage to it.
- The classifiers read source pixels and private locals/virtual stacks. Their results occupy disjoint allocated slots. Dispatch retains y/x/direction order `{5,3,1,7}`. Overlapping source/output storage, small frames, allocation failure, and reference builds retain the original traversal. The contour walkers and destination blending were not parallelized.

Profile and single-frame timings:
- `lockf -k ~/.cache/olm-emu/bench.lock python3 orchestra/reports/P07c-evidence/profile.py`: PF8 and PF16 heavy 4K `sample PID 2 1` and host exits all 0. Samples show `EdgeWalker8/16Exact`, virtual-memory `read32`, and PF16 classifier work. Full sample text is retained compressed.
- Before: registered `~/.cache/olm-emu/P05c-smooth`. After: initial prototype, `build_F47_bundles.py --plugins OLMSmoother --scratch orchestra/state/P07c-smoother-threading/candidate`, successful arm64/x86_64 build.
- Both timing runs used `lockf -k ~/.cache/olm-emu/bench.lock python3 tools/fuzz/ae_realism_audit.py --phase matrix --plugins olmsmoother --cases default corpus00 --situations full 4k --jobs 1 --timeout 60`, with the respective `--cache` and ticket-local `--state`. Each produced 8 OK / 4 existing PF32 refusals. Seconds below are host render seconds, not AE preview measurements.

| Case | Depth | Frame | Before | Initial 32-row prototype |
|---|---:|---|---:|---:|
| default | 8 | 1080p | 0.347016 | 0.171789 |
| default | 16 | 1080p | 0.594188 | 0.235542 |
| default | 8 | 4K | 1.421265 | 0.690064 |
| default | 16 | 4K | 2.449759 | 0.911121 |
| corpus00 | 8 | 1080p | 1.527631 | 1.309066 |
| corpus00 | 16 | 1080p | 1.439943 | 1.123160 |
| corpus00 | 8 | 4K | 7.324758 | 5.201984 |
| corpus00 | 16 | 4K | 7.456678 | 4.496925 |

The 4K before times exceed earlier P05c values and look load-affected. All timing/sample commands held the shared lock; the lock cannot exclude unrelated system activity. PF32 is unsupported, not an exact rendered image.

Correctness:
- `lockf -k ~/.cache/olm-emu/bench.lock python3 tools/perf/ref_vs_fast.py --plugin olmsmoother --parallel 1 2 8 --scratch orchestra/state/P07c-smoother-threading/native`: 200 small + 20 HD + 5 UHD cases; 468 byte-identical comparisons, 207 matching PF32 refusals, 0 mismatches. Includes literal corpus presets and heavy cases. No first differing byte.
- `python3 orchestra/reports/P07c-evidence/campaigns.py`: all commands exit 0, using `--jobs 1`, retained original workers, and Classic contract route. Exact/reject counts:

| Campaign | Exact | Original PF32 rejects |
|---|---:|---:|
| default seed 1 n300 | 205 | 95 |
| realistic-v1 seed 1 n100 | 65 | 35 |
| realistic-v1 seed 20261025 n100 | 59 | 41 |
| realistic-v2 seed 1 n100 | 65 | 35 |
| realistic-v2 seed 20261025 n100 | 59 | 41 |
| odd-even-v1 seed 2026 n150, max 1920×1080 | 92 | 58 |
| Total | 545 | 305 |

Zero Classic mismatches or Mac-only refusals. Default campaign's 600 Classic/Smart status/hash pairs match retained R10 fast evidence: zero exact→non-exact or hash changes. First default Classic hash is `7ffaf5e7bea21fca19688efbf48953d83b57a403abbcc42a0b1ae637d3650644`.
- Standard `tools/fuzz/run.py --replay` with saved max-size/size-sampler flags: root 29/29, P05c stack frames 48/48, T15b odd/even 2/2, P02g realistic 224/224; all 303 `replay_matches_saved=true`. Exact commands are in `oracle__commands.json.gz`.
- `python3 orchestra/reports/P07c-evidence/tsan.py`: 50 integer fuzz-generated frames, resized above the threshold, cap 8; all render successfully with `-fsanitize=thread`, `TSAN_OPTIONS=halt_on_error=1`; no TSan reports. PF32 cases are skipped in favor of supported generated cases. Results and hashes are retained. Two initial script setup errors (missing timeout option; sanitizer flags accidentally passed to the shell build helper) were fixed before this successful run; they did not execute renders.
- `python3 orchestra/reports/P07c-evidence/units.py units-baseline`: 14 module/mode invocations, 7 exits 0, 4 exits 1, 3 exits 5 (no class tests). Existing failures include installed-bundle absence and historical source/evidence hashes. The earlier `units-before` run overlapped the source edit and is invalid as a baseline; it was superseded by this complete run with HEAD source restored temporarily and the candidate restored in `finally`. No candidate-after unit run was completed before the stop decision. Final source is byte-identical to the actual baseline.

Blocking concurrency evidence:
- `python3 orchestra/reports/P07c-evidence/concurrent.py` compiles a Classic test host, then holds the benchmark lock around execution. Four `std::thread` render calls use separate fixtures/state/output; caps are set before launching threads. Opaque checker input at 1920×1080, depths 8/16, tolerances 6/23. All output vectors equal the serial-control output; no deadlock. Each row below is the median of five four-render batches, in seconds.

| Band | Depth | Tolerance | cap 1 | cap 8 | Result |
|---:|---:|---:|---:|---:|---|
| 32 | 8 | 6 | 0.181913 | 0.220649 | slower |
| 32 | 8 | 23 | 0.174602 | 0.217488 | slower |
| 32 | 16 | 6 | 0.244837 | 0.267685 | slower |
| 32 | 16 | 23 | 0.247615 | 0.250125 | slower |
| 128 | 8 | 6 | 0.146290 | 0.150012 | slower |
| 128 | 8 | 23 | 0.158861 | 0.164301 | slower |
| 128 | 16 | 6 | 0.222180 | 0.200482 | faster |
| 128 | 16 | 23 | 0.229409 | 0.223384 | faster |

- Hypothesis 1: 32-row classifier batching improves single frames without a four-frame throughput penalty. Refuted by repeated concurrency measurements.
- Hypothesis 2: amortizing GCD calls over 128-row bands removes that penalty. PF8 remains 2.5–3.4% slower in this run. This also fails the literal no-slowdown condition. Stopped rather than trying more grain/cap combinations.
- Initial single-sample concurrency data is retained separately and is superseded by the repeated measurement. The threshold probe at 256² showed PF8 0.004067→0.003953 s and PF16 0.006204→0.004404 s for the first 32-row run; smaller tested frames stayed sequential. Later threshold measurements vary; this is not an accepted universal crossover.
- An extra four-frame TSan investigation was interrupted deliberately after successful early batches so it would not continue consuming the shared benchmark lock. Its exit 1 is an interrupted run, not a TSan pass or a numerical failure. A potential pre-existing shared debug-coordinate cache was noticed by inspection; no race report was obtained, and it was not changed. The completed 50-case single-frame TSan run above is separate.
- Memory checks observed 55%, 53%, and 51% free, above 30%. Scratch was 9.6 MiB at the final pre-cleanup check and 3.2 MiB after cleanup, far below 5 GiB. All spawned sessions have exited; regenerable binaries/build trees are removed from ticket scratch after evidence retention.
- The initial experimental Universal bundle is registered under `~/.cache/olm-emu/P07c-smooth-initial-experimental/` and `INDEX.json`, explicitly marked NOT accepted / NOT an oracle. `P07c-evidence/cache.json` binds its source and binary hashes.

inference:
- Independent classifier work can accelerate single-frame renders without changing blend arithmetic or order. The remaining contour/fill stages perform ordered overlapping destination updates; independent pixel/row fill is not established.
- More frequent dispatch barriers and duplicated neighbor extraction plausibly explain the MFR overhead; timings alone do not prove the complete cause. Larger bands reduce the measured penalty but do not eliminate it for PF8.
- Load variation is material. It does not justify declaring the measured regressions a pass, nor relaxing the acceptance condition. Native equality is not broader AE-host conformance evidence.

changed_files:
- `orchestra/reports/P07c-smoother-threading.md`
- `orchestra/reports/P07c-evidence/`: three unapplied experimental patches, six Python reproduction/retention scripts, one C++ concurrency fixture, identity JSON, and compressed logs/reports/manifests.
- No production sources or shared helper changes remain. The three unified-diff payloads retain original whitespace in context lines; `git diff --cached --check` flags those payload lines. All three `git apply --check` checks pass.

verify:
- Read-only artifact/patch checks: `git diff --exit-code -- mac/OLMSmoother/Mac/OLMSmoother_port.cpp core/olm_parallel.h tools/perf/ref_vs_fast.py` (empty); `git apply --check orchestra/reports/P07c-evidence/candidate-band32.patch` (exit 0).
- To reproduce the 32-row experiment in an isolated checkout, apply `candidate-band32.patch`, set `S="$PWD/orchestra/state/P07c-smoother-threading"`, `mkdir -p "$S"`, and export `TMPDIR="$S" TMP="$S" TEMP="$S" OLM_TEST_JOBS=1`. Run `python3 orchestra/reports/P07c-evidence/concurrent.py > "$S/concurrent-recheck.log" 2>&1`. Expected: all byte-equality assertions pass; timing results remain measurements, with retained PF8 throughput regressions rather than an acceptance pass. Apply `candidate-band128.patch` instead, from clean source, for the second variant.
- With the 32-row patch applied: `lockf -k ~/.cache/olm-emu/bench.lock python3 tools/perf/ref_vs_fast.py --plugin olmsmoother --parallel 1 2 8 --scratch "$S/native-recheck" > "$S/native-recheck.log" 2>&1`; expected 468 exact / 207 matching refusals / 0 mismatches. The cap-1 bypass in this patch was exercised by concurrency; the original retained full native run used `candidate-initial.patch` as noted above.
- With the 32-row patch applied: `python3 orchestra/reports/P07c-evidence/campaigns.py > "$S/campaigns-recheck.log" 2>&1` and `python3 orchestra/reports/P07c-evidence/tsan.py > "$S/tsan-recheck.log" 2>&1`; expected campaign/replay counts above and 50 successful TSan renders. Run serially; do not overlap with timing runs.
- Baseline matrix: `lockf -k ~/.cache/olm-emu/bench.lock python3 tools/fuzz/ae_realism_audit.py --phase matrix --cache "$HOME/.cache/olm-emu/P05c-smooth" --state "$S/baseline-recheck" --plugins olmsmoother --cases default corpus00 --situations full 4k --jobs 1 --timeout 60 > "$S/baseline-recheck.log" 2>&1`. Substitute cache `P07c-smooth-initial-experimental` and a new state directory for the initial candidate. Expected 8 OK / 4 PF32 refusals each; timing values may vary.

next:
- Orchestrator decision needed on a follow-up specifically addressing MFR scheduling overhead or a revised performance acceptance criterion; this ticket does not waive the requirement.
- Do not merge/apply the experimental production patch as accepted. A follow-up needs full final-source verification, after-unit comparison, an accepted threshold, and passing four-frame throughput measurements.
