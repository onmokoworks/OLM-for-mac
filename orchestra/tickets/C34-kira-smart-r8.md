## Goal
Reduce the **Smart-route** residual of **olmkirakira** (F18: Smart is the route AE uses).
Current seed-1 n300 Smart residual: 275 exact / 0 mismatch / 25 refusal (after C29; 13 are original AEX rejects)

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
- Default oracle is the F32 worker. The Mac float math uses `ucrtmath`; `core/x86_float.h` has the x86 generated-NaN helpers.
- Divergence at a still-host math import: label it `ucrt-math-pending`. Work-budget refusals: label them, do not change the budget.
