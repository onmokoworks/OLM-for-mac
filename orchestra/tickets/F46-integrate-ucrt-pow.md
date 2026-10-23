# F46: integrate double ucrt_pow (worker + Mac + default oracle)

## Facts
- F43c (merged) implemented `ucrt_pow` in `ucrtmath/ms/pow.c`, bit-exact against UCRT in both
  modes. Its report says "blocked" only because a cleanup command was rejected by tool policy;
  the numerical work is complete. Orchestrator re-check: 300k mixed pairs, 0 mismatches.
- F45 integrated double sin/cos/exp and left pow on host by its fallback rule.
- F45 found that DistanceGradation's Gaussian exp is embedded softdouble, not the import. Apply
  the same boundary audit to pow.
- Double pow import users (plugins_2025): Smoother2 (pow), OLMBlur (pow), DistanceGradation (pow).

## Do
Follow F45 exactly, for pow:
1. Build an F46 worker from F45 with `pow` routed to `ucrt_pow` (FMA), for both DLL names and both
   paths. Add an INDEX entry. Validate the shim with 10^6 random pairs and 10^6 plugin-range pairs
   against the Rosetta oracle, expecting 0 mismatches.
2. Switch only the Mac call sites that correspond to the *imported* pow. Run the static
   boundary audit for embedded math.
3. Make the new worker the default and keep F45 selectable.
4. Measure seed 1 plus one fresh seed, n300, for all 10 plugins, and replay every corpus. No
   exact case may be lost; rebaseline only for demonstrated pow reasons.
- Use 1-2 processes. Check `memory_pressure` before the Rust build. Do not touch the release gate/ledger.
