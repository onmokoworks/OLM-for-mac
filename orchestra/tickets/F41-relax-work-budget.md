# F41: relax the Mac work-budget caps to Windows-like behaviour (user-approved)

## Decision (user, 2026-10-23)
Relaxing the Mac-only work-budget refusals is approved. The original Windows AEX has no such cap.
C26/C33 showed that budget bypass turns refusals exact (RadialBlur `smartrender-generic-budget`, etc.).

## Do
1. Inventory every Mac-side work/size budget refusal across all plugins: grep `budget`,
   `OUT_OF_MEMORY` refusals and `*_REFUSAL("...budget...")` tags. Example:
   `mac/OLMRadialBlur/OLMRadialBlur.cpp` `CheckedRadialGenericBudget`.
2. For each one, decide its fate:
   - **Remove or relax** caps that only limit work amount.
   - **Keep** checks that protect against integer overflow or impossible allocations.
     Convert them to exact overflow checks, so that allocation failure becomes an honest
     `PF_Err_OUT_OF_MEMORY` only when it actually happens.
   - **Respect the original:** if the original AEX itself refuses or fails at a size, match it.
     Check the oracle's `aex_budget` / `aex_reject` results and the decomp.
   - Keep AE responsive. Long renders are acceptable, because AE handles interruption via
     `PF_ABORT`. If a loop has no abort check where the original had one, add the original's
     abort polling.
3. Measure seed 1 n300 and one fresh seed for every affected plugin. Every newly admitted output
   must be exact; mismatch → refusal is fine. No exact case may be lost. Corpora must replay.
4. Report the before/after E/M/R/U and the list of removed or kept guards with their reasons.
- Use 1-2 processes. Keep fuzz case timeouts as they are, and report cases that time out. Do not touch the release gate/ledger.
