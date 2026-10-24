# P07a: shared deterministic parallel helper + KiraKira in-frame threading

## Plugin facts
- KiraKira default: 0.43 s per 1080p frame and 1.7 s at 4K, at all depths (P00b). It is the slowest default among the fast plugins.
- First create `core/olm_parallel.h`: a small header-only helper (`olm::parallel_rows(count, min_grain, fn)`) built on `dispatch_apply_f`. It needs an `OLM_PARALLEL_MAX` override for tests and a sequential fallback. Then migrate `core/dblur_rowdriver.cpp` and `core/olmblur_parallel_parts.h` onto it **only if** that is a no-op refactor with identical hashes; otherwise leave them.
- Then thread KiraKira's dominant stages.

## Goal
- Make a single frame render faster by using several CPU cores **inside** the render call. The output must stay **bit-identical**.
- AE already renders different frames in parallel (multi-frame rendering; all ten plugins set `PF_OutFlag2_SUPPORTS_THREADED_RENDERING`), so this mainly speeds up preview and scrubbing, where a single frame is the wait.

## Determinism rules (hard)
- Every output value is computed by exactly one task, with the same arithmetic and the same operand order as the sequential code.
- Never parallelize a floating-point reduction or accumulation whose order would change. Allowed: independent rows, tiles or channels; reductions that are order-insensitive (integer sum, min/max); and a fixed-order final combine that reproduces the sequential order exactly.
- No shared mutable state between tasks except disjoint output ranges. Respect the ledger restrictions for the plugin.
- Use GCD `dispatch_apply_f` on `QOS_CLASS_USER_INITIATED`, as `core/dblur_rowdriver.cpp:224` already does (it cooperates with AE's own threads). Use the shared helper `core/olm_parallel.h` once P07a creates it. Skip threading for small frames: below a measured pixel threshold, keep the sequential path.
- Verify: same output hashes with forced thread counts 1, 2 and 8 (add an env/test hook such as `OLM_PARALLEL_MAX`), plus a ThreadSanitizer build of the test host over 50 fuzz cases with no reports. Also run 4 renders concurrently (to simulate AE multi-frame rendering): no deadlock and no slowdown versus sequential.

## Measure
- Use the P00b driver (`tools/fuzz/ae_realism_audit.py --phase matrix --situations full 4k`) at 8/16/32 bpc with the default params and the heaviest corpus case for this plugin, before and after.
- Profile with `sample` first, and parallelize the stages that dominate.

## Acceptance (per plugin touched)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 and realistic-v2, seed 1 + a fresh seed, n100 each; odd-even-v1 (T15b flags) seed 2026 n150. All with 0 mismatches and 0 Mac-only refusals, beyond those already documented.
- All corpora of the plugin replay true under standard `tools/fuzz/run.py --replay`, with matching flags.
- Unit tests before and after (`OLM_TEST_JOBS=1`).
- A before/after timing table.

## Rules
- Use 1-2 processes for fuzz and builds. Benchmarks must run alone; check `memory_pressure` (≥30% free).
- Change only this plugin's sources, its plugin-only core helpers, and `core/olm_parallel.h`.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, and do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.
