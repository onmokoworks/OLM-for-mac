# OLMDistanceGradation dominant-channel all-modes probe (deferred)

Date: 2026-07-09

## Decision

Deferred / not adopted. The probe is useful evidence because it reduces focused `case_0014` from max `4` to max `2`, but it does not reach exact and is not binary-grounded. The source was reverted to the BOTH-only rule until a narrower discriminator or canonical batch proof exists.

Important correction: the full 16-case single-case run must **not** be read as proof that the probe broke `case_0010/case_0011`. After reverting the source and reinstalling the BOTH-only build, `refs/reports/ae_single_case_olmdistancegradation_reverted_both_rule_spotcheck_20260709/` still reports `case_0010 max=2` and `case_0011 max=2` under the same single-case runner. That makes those rows runner/context artifacts, not implementation-break evidence.

## Probe

- Candidate: generalize the 16bpc+ low-alpha dominant-channel mask from `IN_OUT_BOTH` only to all in/out modes.
- Candidate output root: `refs/reports/ae_single_case_olmdistancegradation_dominant_all_modes_full16_20260709/`
- Reverted spot-check root: `refs/reports/ae_single_case_olmdistancegradation_reverted_both_rule_spotcheck_20260709/`
- AE note: AE 2026 repeatedly exited between single-case runs; cases were retried after relaunch. Produced PNGs were compared, but this runner is not the authority for 16bpc exact counts.

## Full single-case comparison (diagnostic only)

Single-case exact count: 5/16 (diagnostic only; do not use as conformance status)

| case | status | max | nonzero px | mean abs | baseline max | baseline nonzero px |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 0008 | exact | 0 | 0 | 0.000000000 |  |  |
| 0010 | diff | 2 | 351 | 0.000169271 |  |  |
| 0011 | diff | 2 | 501 | 0.000241609 |  |  |
| 0012 | diff | 2 | 2948 | 0.001990500 | 2 | 2948 |
| 0013 | diff | 2 | 7052 | 0.003813175 | 2 | 9006 |
| 0014 | diff | 2 | 7415 | 0.003856096 | 4 | 9630 |
| 0016 | diff | 2 | 1899 | 0.001307147 | 2 | 5373 |
| 0020 | exact | 0 | 0 | 0.000000000 |  |  |
| 0021 | exact | 0 | 0 | 0.000000000 |  |  |
| 0022 | exact | 0 | 0 | 0.000000000 |  |  |
| 0023 | exact | 0 | 0 | 0.000000000 |  |  |
| 0024 | diff | 20 | 1051915 | 0.327421152 |  |  |
| 0025 | diff | 6 | 860084 | 0.289623119 |  |  |
| 0026 | diff | 4 | 900709 | 0.268155744 |  |  |
| 0027 | diff | 4 | 451535 | 0.117609713 |  |  |
| 0028 | diff | 3080 | 457177 | 7.260353250 |  |  |

## Interpretation

- FACT: The all-modes probe changes the retained `case_0014` witnesses from store RGB word `18117` to `18119`, matching the direction expected from the Windows PNG residual and reducing the case max from `4` to `2` in the focused run.
- FACT: The probe still leaves `case_0012/0013/0014/0016` non-exact (`max=2` family).
- FACT: Reverted BOTH-only spot-check still reports `case_0010/0011 max=2` under `scripts/run_ae_single_case.py`, so this runner cannot adjudicate whether the probe regresses previously exact canonical-batch cases.
- INFERENCE: The correct rule may be narrower than all in/out modes, or the remaining family may be dominated by PF16 store/export rounding. Do not adopt this broadening from PNG-only evidence.
- Next proof: keep the current BOTH-only implementation and pursue binary/store/export evidence for representative `case_0012` +/-2 and `case_0014` -4 pixels, or rerun the canonical 16bpc batch with the candidate in a controlled branch before considering adoption.

