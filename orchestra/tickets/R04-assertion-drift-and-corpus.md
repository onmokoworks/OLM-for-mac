# R04: tests that assert superseded admission policy + Kira legacy corpus transitions

## Facts (I03 report)
- (a) Admission assertion drift, 5 generic entries: R02 (ColorKeep generic/ROI negative assertions expect DEEP-flag
  refusals the original never had) and F41b (Blur lane, Distance pf32-unblurred, Radial budget assertions expect work/size
  caps that were relaxed to match Windows). Parent passes / merge fails for each.
- KiraKira corpus: 64 legacy result transitions (23 top-level Smart refusal→exact; nested T06: 23 refusal→exact,
  18 mismatch→exact; nested Classic 31 mismatch→refusal, 10 mismatch→mismatch) and old files lack `oracles` metadata.
- `test_run_olm_generic_beta_gate.py`: real pytest skipif not honored by the lightweight loader.

## Do
1. Rewrite each drifted assertion to the current, original-matching contract, equally strict: where the old test asserted
   a refusal, assert the original-AEX-matching behaviour (exact output vs reference, or the specific refusal that remains).
   Cite the merge that changed the policy in a comment.
2. Rebaseline the Kira corpus with `rebaseline_corpus.py` (`--production-rebaseline R04` / `--route-correction` as
   appropriate). Only toward exact on Smart; list every file. Add missing `oracles` metadata via replay, not by hand.
3. Fix the skipif interop in the gate loader.

## Rules
OLM_TEST_JOBS=2. No plugin production changes; do not touch link recipes (R03 runs in parallel).
