# C56-dg-smart-r3

## Goal
Reduce the **Smart-route** residual of **olmdistancegradation** (F18: Smart is the route AE uses).
Current seed-1 n300 Smart residual: seed1 290 exact, seed105 285 exact (C54); every AEX-successful case in those seeds is exact. Measure seed 1, seed 105 and one fresh seed.

## Loop (repeat until 3 clusters are closed, or the time budget of ~3h, or blocked)
1. Re-measure: `tools/fuzz/run.py --plugin olmdistancegradation --n 300 --seed 1 --jobs 1` with scratch corpus.
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
- Start from C54 next: Mac timeouts first (seed1/10 Bilateral, seed105/205,296 Median): make the Mac faster without changing arithmetic (like C54's exact-certified Box sums). Then PF32 Bilateral radius 2, scalar radius>500, vector/HDR/Power combos. Original Median assertions are an original-OLM behaviour: document what AE would see.
