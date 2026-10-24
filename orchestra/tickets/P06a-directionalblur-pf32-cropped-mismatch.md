# P06a: DirectionalBlur PF32 signed input + downsample 1/3 + cropped request: pre-existing Smart mismatch

## Witness (P05a, `orchestra/reports/P05a-directionalblur-performance.md`, "Blocking boundary")
- realistic-v1 seed 2053, index 9: PF32 signed input, input 7x5, full layer 19x15, downsample 1/3, request `[6,1,7,3]`.
- 6 of 8 float words differ. First expected word bytes are `2ba6b6bd`, actual `8c9cd9be`. Original output SHA256 is `cad415cd...`.
- Present before P05a (the orchestrator reproduced it on main before the merge), so it is not caused by the optimization. Retained witness: `tests/fuzz_corpus/olmdirectionalblur/P05a-performance/preexisting-*`.
- These are not 1-ULP differences: the values differ in sign and magnitude, so suspect geometry (which source pixels feed which output). Candidates are the crop offset, the downsample-scaled distance with a non-zero request origin, or edge handling for negative/signed values at PF32.

## Do
- Shrink the witness. Dump paired intermediates (source sampling coordinates, the scaled distance, row/offset mapping) from the original on F52c and from Mac. Use disassembly (`decomp/OLMDirectionalBlur.aex.c.txt`, P02j excerpts) to find the cause. Fix it in the general path.
- Then run a wider PF32 + downsample + cropped-request sweep (realistic-v1 and v2, PF32-heavy if the sampler allows, at least 3 seeds n100) to make sure the class is closed.

## Acceptance (common)
- The contract route (Smart; Classic for Smoother v1) stays exact: default fuzz seed 1 n300 with no exact→non-exact; realistic-v1 and realistic-v2, seed 1 + seed 2053 + a fresh seed, n100 each, and odd-even-v1 (T15b flags) seeds 2026/2027 n150 with 0 mismatches and 0 Mac-only refusals.
- All of this plugin's corpora replay true under standard `tools/fuzz/run.py --replay` (both routes, matching flags; T15b sets need `--size-sampler odd-even-v1 --max-size <summary maximum>`).
- Unit tests before/after (`OLM_TEST_JOBS=1`). Add new witnesses as a labelled corpus set.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free). Change only DirectionalBlur sources and its plugin-only core helpers.
- Keep the P05a performance: re-time corpus09 at 1080p/4K with the P00b driver, and do not regress by more than 10%.
- Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- Commit partial results at least every 30 minutes. The stop rule applies.
