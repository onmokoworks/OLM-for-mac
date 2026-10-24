# P05b: RadialBlur rotation mode speed: >60 s per 1080p frame with heavy params

## Facts (P00b report)
- With `tests/fuzz_corpus/radialblur/C45_seed1_case000108.json` params (rotation mode), 240x135 takes 36-38 s and 480x270 exceeds 60 s, so 1080p is far beyond. Defaults are fast.
- Hot functions: `SampleScalarAEXNoRepeat`, `RadialAEXSinHot` and `RenderRotationTyped`.
- First establish how work scales with size and params (samples per pixel, per-sample sin evaluations) and whether that matches the original's algorithm. Sin values of loop-invariant angles can likely be precomputed once per angle with identical bits.

## Performance goal
- The original cannot be timed natively here, so the goal is practical: a 1080p frame with heavy corpus params under about 2 s, and 4K under about 8 s, on this M1 Pro, while staying **bit-exact**.
- Optimizations must preserve every arithmetic result: operation order, float precision, rounding, NaN and signed-zero behaviour, and accumulation order. Valid techniques: removing invariant or redundant work, hoisting, better memory layout, skipping provably dead work, and multi-threading over independent rows/tiles with deterministic per-pixel results.
- Approximate math, tolerance or a refusal budget are not allowed.
- Measure before and after with the P00b driver (`tools/fuzz/ae_realism_audit.py`) and `sample` profiles. Report the timing table.

## Acceptance (common)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 seed 1 + a fresh seed n100 and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.
