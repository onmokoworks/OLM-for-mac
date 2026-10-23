# C47: DistanceGradation — the S01 Smart mismatch (seed104 case207, PF8)

## Facts
S01 found the only DG Smart mismatch in 1,500 cases: seed 104 case 207, PF8, 140×159, first differing word 93
(Mac 0xc4 vs ref 0xc5), 2558 differing words. Witness: `tests/fuzz_corpus/olmdistancegradation/seed104_case000207_S01.json`.
Shrinking accepted nothing, so the trigger is the parameter combination, not the geometry.

## Do
1. Replay the witness; find the FIRST divergent stage vs the original AEX (reuse the DG paired-trace tools in tools/emulation/).
2. Fix the general operation. If a root-cause fix is not reachable in budget, narrow admission so the case (and its domain) is refused — admitted outputs must be exact.
3. Re-measure seed 1 and seed 104 n300 Smart; replay the DG corpus.

## Acceptance
No exact→non-exact on seed 1 / 104 or the corpus. The witness becomes exact (preferred) or refused.

## Notes (orchestrator)
- All math imports are UCRT-exact; `core/x86_float.h` has the NaN helpers; work-budget is relaxed (F41b); out-of-range noise-table reads return 0 (C45, `notes/KNOWN_ORIGINAL_BUGS.md`).
- If a refusal domain turns out to be another original-OLM bug (undefined reads, uninitialised memory), propose deterministic semantics in the report and add it to KNOWN_ORIGINAL_BUGS.md. Implement it if the oracle agrees on the observed values.
- S01 (`orchestra/reports/S01-wide-mismatch-sweep.md`) measured seeds 101-105; its per-seed reports are in `orchestra/reports/S01-wide-mismatch-sweep/*.json.gz`.
