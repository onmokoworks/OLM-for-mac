# C48: RadialBlur — the S01 Smart mismatch (seed102 case8, PF32)

## Facts
S01 found the only RadialBlur Smart mismatch in 1,500 cases: seed 102 case 8, PF32. Original 1×217
(word 120: Mac 0x3eb5863d vs ref 0x3f0ee30a, 2 words); shrunk 1×54 (word 116, 12 words; the ref is ~2× Mac).
Witness: `tests/fuzz_corpus/radialblur/seed102_case000008_S01.json`. 1-pixel-wide geometry is suspicious
(edge/sample-count/weight normalisation).

## Do
1. Replay the witness and the original case; find the FIRST divergent stage vs the original AEX (Radial paired-trace tools).
2. Fix the general operation, or narrow admission so the domain is refused (admitted outputs must be exact).
3. Re-measure seed 1 and 102 n300 Smart; replay the Radial corpus.

## Acceptance
No exact→non-exact on seed 1 / 102 or the corpus. The witness becomes exact (preferred) or refused.

## Notes (orchestrator)
- All math imports are UCRT-exact; `core/x86_float.h` has the NaN helpers; work-budget is relaxed (F41b); out-of-range noise-table reads return 0 (C45, `notes/KNOWN_ORIGINAL_BUGS.md`).
- If a refusal domain turns out to be another original-OLM bug (undefined reads, uninitialised memory), propose deterministic semantics in the report and add it to KNOWN_ORIGINAL_BUGS.md. Implement it if the oracle agrees on the observed values.
- S01 (`orchestra/reports/S01-wide-mismatch-sweep.md`) measured seeds 101-105; its per-seed reports are in `orchestra/reports/S01-wide-mismatch-sweep/*.json.gz`.
