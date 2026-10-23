# F41b: relax work-budget caps on the Smart route (continuation of F41)

## Clarification (orchestrator)
F41 (`orchestra/reports/F41-relax-work-budget.md`) stopped because RadialBlur relaxation exposed
four **Classic** mismatches. AE calls only Smart for 9 of the 10 plugins; Smoother v1 is
Classic-only (F18). Classic residuals on those 9 plugins are not acceptance criteria:
Classic has about 120 pre-existing mismatches already.
- Relax **Smart** budget caps only. Keep the Classic guards exactly as they are, refusing as
  now, for the 9 Smart plugins.
- "Two unverified Smart outputs": if the oracle times out or hits its own budget on these, rerun
  only those cases with a larger `--case-timeout`. If the oracle still cannot render them,
  keep the Mac refusal for that domain and label it.
- Policy size caps (4096×2160, 3.6B work units, etc.) that only exist on the Mac side: remove
  them on Smart. Keep the multiplication/allocation overflow checks as exact checks.
- Abort: AE Smart render gives `PF_ABORT` / progress callbacks. Where the original polls
  abort (check the decomp), poll it too. Do not add watchdog timers.

## Do
Apply the above plugin by plugin, starting with RadialBlur, then Blur and the rest of F41's
inventory. Use one commit per plugin.
- After each commit, run seed 1 plus one fresh seed, n300, on Smart. No exact case may be lost,
  and every newly admitted output must be exact. Also replay the corpus.
- Report before/after Smart E/M/R/U per plugin.
- Use 1-2 processes. Do not touch the release gate/ledger.
