# C55-kira-smart-r2

## Goal
Reduce the **Smart-route** residual of **olmkirakira** (F18: Smart is the route AE uses).
Current seed-1 n300 Smart residual: seed1 287/0/13, seed105 285/0/15, seed106 283/0/17 (C50). Measure seed 1 and seed 106.

## Loop (repeat until 3 clusters are closed, or the time budget of ~3h, or blocked)
1. Re-measure: `tools/fuzz/run.py --plugin olmkirakira --n 300 --seed 1 --jobs 1` with scratch corpus.
2. Pick the largest remaining Smart cluster (mismatch or refusal of an AEX-rendered case).
3. Mismatch: find the FIRST divergent stage vs the original AEX (reuse existing paired-trace tools in
   tools/emulation/ for this plugin; build one if absent) and fix the general operation.
   Refusal: gate-off experiment; promote only general rules proven exact (seed 1 + fresh seed),
   sanitizer clean, zero admitted mismatches (F10/F12 method).
4. Commit each closed cluster separately with its before/after numbers.
Read first: the plugin's triage and fix reports in orchestra/reports/ (grep the plugin name).

## Acceptance (per commit)
No base-exact Smart case may change. Smart exact must not decrease. Corpus replay changes only
toward exact (rebaseline with a before/after table). Sanitizer clean. Cause outside the port
(Windows dependency/host/oracle) -> document and move to the next cluster.

## Notes (orchestrator)
- All math imports are UCRT-exact; `core/x86_float.h` has the NaN helpers including `sse_add/sub/mul/div/min/max` (F49: SSE first-NaN-operand propagation, MINSS/MAXSS second-operand selection); work-budget is relaxed (F41b).
- If a refusal domain turns out to be an original-OLM bug (undefined reads, uninitialised memory), propose deterministic semantics and add it to notes/KNOWN_ORIGINAL_BUGS.md; implement it if the oracle agrees.
- Start from C50 next: finite scalar/color Gaussian source admission (seed106/122,123,248; S01 seed102/20,55, seed103/26,46). Gate off and trace before promotion.
