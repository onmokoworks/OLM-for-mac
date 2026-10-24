# P03a: DistanceGradation PF32 + downsample: 1-ULP field mismatches

## Witnesses (T15b, `orchestra/reports/T15b-odd-even-random-comp-sweep.md`, section "DistanceGradation: four admitted PF32 scaled-field mismatches")
- 4 admitted Smart mismatches out of 300, all PF32, Inside, Linear, no blur, non-unit downsample (mostly 1/4, one 1/8). Raw words differ by 1 ULP (e.g. original `24ea213f`, Mac `25ea213f`).
- Reduced witnesses are saved in `tests/fuzz_corpus/olmdistancegradation/T15b-odd-even-realistic/` (smallest 12x8 at 1/8). Replay with `--geometry realistic --size-sampler odd-even-v1 --max-size <maximum from T15b-evidence/olmdistancegradation-summary.json>`.
- Changing only downsample to 1/1 (same pixels, params, ROI, padding) makes all four exact, so the cause lies in the downsample-scaled field staging: `core/olmdistancegradation_fieldgen.cpp:114-159` (mask expansion, EDT, linear resize at :125, float row combine at :138, normalize at :159) and `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:2141` (dimension reconstruction).

## Do
- Find the original's float arithmetic for the downsample-scaled field from disassembly (`decomp/OLMDistanceGradation.aex.c.txt` and the AEX), especially how the scaled distance or resize factor is formed (float32 vs double, operand order, num/den use; see P01/P02b notes for the float32 X-factor pattern).
- If possible, dump paired intermediates (scaled field before normalization) from oracle and Mac for the 12x8 witness rather than tuning from final bytes. The ledger forbids broad EDT/writer retuning driven only by residuals.

## Acceptance
- All four witnesses exact. Realistic + odd-even-v1 sweep for DistanceGradation (seeds 2026, 2027, n150): 0 mismatches and 0 Mac-only refusals beyond the nonfinite/HDR cases handled in P03b.
- Default fuzz (seed 1, n300): no exact→non-exact. All DistanceGradation corpora replay true (standard run.py, matching flags). Unit tests before/after (`OLM_TEST_JOBS=1`).

## Rules
- Use 1-2 processes. Change only DistanceGradation sources and its plugin-only core helpers. Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- The stop rule applies.
