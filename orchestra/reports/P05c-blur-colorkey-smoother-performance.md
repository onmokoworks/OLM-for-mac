status: partial
summary:
- Blur: preserve all scalar arithmetic; execute six independent parts on two joined lanes at dimensions >=256x256.
- Heavy Blur corpus05 is now 1.61–1.75 s at 1080p and 6.41–6.86 s at 4K in the P00b SDK host.
- Final Smart campaigns: 800/800 exact; all 60 saved corpora replay true. Unit modules: 7 pass / 27 fail both before and after (pre-existing evidence/asset failures).
- Rejected volatile-removal optimization changed NaN payloads and was fully reverted.
- ColorKey cache and differential/performance checks complete; full post-change unit suite still running. See `P05c-evidence/colorkey.md`. Smoother remains pending.

facts:

Baseline commit: `00b91897d2fee8ba1b100af4f83dff6adeacbad2`. Initial `memory_pressure`: 60% free; later check: 54%. Processes were limited to two concurrent build/render/oracle lanes, each fuzz `--jobs 1`.

Blur timings are single render-selector measurements on the shared machine, using fresh Universal Release bundles and `tools/fuzz/ae_realism_audit.py --phase matrix --plugins olmblur --cases corpus05 --situations full 4k --jobs 1`. Both before and after: 6 OK / 0 refusals. This is an SDK host, not native AE timing.

| Depth | Before 1080p | After 1080p | Before 4K | After 4K |
|---|---:|---:|---:|---:|
| PF8 | 3.008953 | 1.612375 | 11.934466 | 6.407640 |
| PF16 | 3.011834 | 1.752795 | 12.039747 | 6.462367 |
| PF32 | 3.017570 | 1.690880 | 12.395997 | 6.864674 |

- `sample PID 2 1 -file PATH`: before and final samples succeeded (return 0). Before: horizontal/vertical helpers dominate; final profile records joined parallel helper execution. Raw profiles, timing rows, manifests and cache hashes are in `P05c-evidence/blur-*`.
- Baseline default seed 1 n300: Smart 300 exact. Final: default seed 1 n300, realistic-v1 seeds 1/20261024 n100 each, odd-even-v1 seeds 2026/2027 n150 each at max 1920, height max 1080: Smart 800 exact, 0 mismatches, 0 Smart refusals. Classic refusals are preserved and are outside this plugin's contract route.
- Standard replay: root corpus 39/39, T15b corpus 3/3, P05c threshold corpus 18/18; `replay_matches_saved=true` for all three, including both routes. P05c covers 255x257, 256x256, 257x259, both bias directions and all three depths using actual AEX outputs.
- `python3 orchestra/reports/P05c-evidence/units.py olmblur units-before` and the corresponding `units-after`: 34 modules each, exactly the same 27 nonzero returns. Logs retain missing handoff/build-identity artifacts and missing `plugins_2025/OLMBlur.aex` errors; these results are not presented as passing unit tests.
- Supplementary module-level tests (unittest does not discover these): `check_blur_functions.py` temporarily uses the pre-ticket worker sources, restores the committed candidate in `finally`, then reruns. Before/after: 3 modules, the same 1 failure; detailed logs retained.
- `compare_blur_helper.py`: original volatile-removal experiment failed at rounding=0, iteration=2, horizontal word=12: old `ffc00000`, candidate `ffc12345`. That source change was reverted. Reproduce this rejected experiment with `compare_blur_helper.py --rejected-volatile-removal` (expected exit 1 and the same first differing word). Final unchanged scalar helper plus parallel dispatch comparison: 4,310,640 exact words, 3,200 scalar and 8 parallel comparisons, four rounding modes. No mismatching word in final comparison.
- Final dispatch propagates the caller's floating-point environment to each lane and restores the worker environment. Each pass joins before the next pass reads its destination.
- Fresh baseline/final bundles retained and registered at `~/.cache/olm-emu/P05c-blur-before` and `~/.cache/olm-emu/P05c-blur`; host remains an absolute link to P00b. Identity hashes are in `P05c-evidence/blur-cache.json`.

inference:
- The measured gain comes from independent row/column execution; scalar helper operations, weights, accumulation order, writers, and UCRT math are unchanged.
- Volatile removal allowed a different NaN operand selection despite ordinary SDR fuzz passing. This is evidence against removing those qualifiers without stronger arithmetic constraints, not an AEX NaN conformance claim.
- Baseline unit evidence failures prevent claiming an entirely green test suite; identical module outcomes establish only no observed module-status regression.

changed_files:
- core/olmblur_parallel_parts.h
- core/olmblur_worker_orchestration.cpp
- core/olmblur_worker16_nonlegacy.cpp
- core/olmblur_worker32_nonlegacy.cpp
- tests/fuzz_corpus/olmblur/P05c-parallel-boundary/*.json
- orchestra/reports/P05c-evidence/*
- orchestra/reports/P05c-blur-colorkey-smoother-performance.md

verify:
```sh
python3 orchestra/reports/P05c-evidence/check_blur.py
python3 orchestra/reports/P05c-evidence/compare_blur_helper.py
python3 orchestra/reports/P05c-evidence/units.py olmblur units-recheck
python3 orchestra/reports/P05c-evidence/check_blur_functions.py
python3 tools/fuzz/run.py --plugin olmblur --geometry realistic --size-sampler odd-even-v1 --max-size 1920 --replay tests/fuzz_corpus/olmblur/P05c-parallel-boundary --jobs 1 --scratch orchestra/state/P05c-blur-colorkey-smoother-performance/recheck-witness --report orchestra/state/P05c-blur-colorkey-smoother-performance/recheck-witness.json
python3 tools/fuzz/ae_realism_audit.py --phase matrix --cache "$HOME/.cache/olm-emu/P05c-blur" --state orchestra/state/P05c-blur-colorkey-smoother-performance/recheck-performance --plugins olmblur --cases corpus05 --situations full 4k --jobs 1
```
Expected: campaign Smart counts 300/100/100/150/150 exact; three corpus sets true; helper 4,310,640 exact words; unit statuses as baseline, not all green; six performance rows OK. Set `TMPDIR`, `TMP`, `TEMP` to the ticket scratch and `OLM_TEST_JOBS=1` when invoking fuzz directly.

next:
- Finish ColorKey post-change unit suites, then Smoother; each needs independent evidence and commit.
- Separate environment follow-up: restore historical unittest evidence dependencies without modifying MAIN or changing numerical expectations.
