# C54-dg-smart-r2

## Goal
Reduce the **Smart-route** residual of **olmdistancegradation** (F18: Smart is the route AE uses).
Current seed-1 n300 Smart residual: seed1 290/0/3/1/6, seed105 283 exact / 3 refusal (C52). Measure seed 1 and seed 105.

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
- All math imports are UCRT-exact; `core/x86_float.h` has the NaN helpers; work-budget is relaxed (F41b).
- Read `orchestra/reports/C52-dg-smart-r1.md` first: its `next` lists the remaining finite unblurred Power and large-Box refusals; larger Bilateral is unproven. S01 unresolved = original Median assertions / original timeouts / Mac timeouts (F50 is making oracle stops deterministic in parallel; do not touch workers).
- Mac timeouts are ours to fix: if a Mac render exceeds the case timeout where the original finishes, profile it and make it faster without changing arithmetic.
