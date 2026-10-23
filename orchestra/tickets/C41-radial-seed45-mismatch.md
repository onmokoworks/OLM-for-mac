# C41-radial-seed45-mismatch: resolve the admitted Smart mismatch witness for radialblur

## Facts
- Witness: `tests/fuzz_corpus/radialblur/seed45_case000008_C39.json`, saved as a known mismatch by C39. Read `orchestra/reports/C39-seed45-residual-mismatches.md`.
- pre-existing before F41b (orchestrator-checked); plane capture incomplete in C39.

## Required outcome (one of two, both acceptable)
A. Find the first divergent stage and fix the general cause, so the witness becomes exact.
B. If A is not reached after two refuted hypotheses: **narrow the Smart admission** so the
   witness's domain is refused. Use the smallest general predicate that covers it, derived
   from the parameters/inputs that reach the divergent stage, not a per-case match.
   mismatch → refusal is an allowed transition. This fallback is mandatory; do not end
   without A or B.

## Verify
- Run seeds 1, 44, 45 and one fresh seed, n300 each, for radialblur: 0 Smart mismatches, and no exact
  case lost compared with the current baseline. Report the cost in exact cases if you chose B.
- Replay the corpus. Rebaseline only the witness: mismatch → exact or refusal.
- Use 1-2 processes. Do not touch the release gate/ledger.
