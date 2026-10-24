# P05c: OLMBlur, ColorKey and Smoother speed at heavy params

## Facts (P00b report)
- OLMBlur, corpus05: 2.9 s at 1080p and 11.7 s at 4K. Hot functions: `olm::blur::horizontal` and `vertical`.
- ColorKey, corpus05: 1.9 s at 1080p and 7.4 s at 4K. Hot functions: `ucrt_powf`, `RGBToPluginLab76` and `ucrt_atan2f`. Look for repeated Lab conversions of the same colour (key colours, per-pixel recomputation) before touching the math. Replacing the UCRT math is not allowed.
- Smoother v1, PF16 corpus00: 2.2 s at 1080p and 8.6 s at 4K. Hot functions: `_platform_memset`, `SubHandler8Memory::read32`, `EdgeWalker16Exact` and `Classifier16Exact`. Look for redundant clears and address translation.
- Do the plugins in this order: Blur, ColorKey, Smoother. Each one is a separate commit with its own before/after table, and each must meet the acceptance on its own.

## Performance goal
- The original cannot be timed natively here, so the goal is practical: a 1080p frame with heavy corpus params under about 2 s, and 4K under about 8 s, on this M1 Pro, while staying **bit-exact**.
- Optimizations must preserve every arithmetic result: operation order, float precision, rounding, NaN and signed-zero behaviour, and accumulation order. Valid techniques: removing invariant or redundant work, hoisting, better memory layout, skipping provably dead work, and multi-threading over independent rows/tiles with deterministic per-pixel results.
- Approximate math, tolerance or a refusal budget are not allowed.
- Measure before and after with the P00b driver (`tools/fuzz/ae_realism_audit.py`) and `sample` profiles. Report the timing table.

## Acceptance (common, per plugin touched)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 seed 1 + a fresh seed n100 and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.
