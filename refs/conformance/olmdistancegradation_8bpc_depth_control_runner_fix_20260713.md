# OLMDistanceGradation 8bpc depth-control runner fix (2026-07-13)

## Decision

The desktop return is `exact_bind_failure` before the AE pause handshake. It
contains no callback hit and no algorithm evidence. Resending the same v3
package would repeat an unobservable launch failure.

## Returned facts

- Return SHA-256:
  `984f0efea8a2f8cdd60054940805fec9a3586ddae834450b508878856ecc0ca2`
- Failure stage: `depth_control`
- Missing prerequisite: `ae_ready.marker`
- Last observation: launcher PID `12708`, launcher exited, no matching AfterFX
  process, and no AE log.
- The fail-closed classifier rejects the return because its status is not
  `answered`.

## Replacement contract

The v4 runner records launcher exit state and stdout/stderr, AE log/result,
desktop session, and matching-process diagnostics on every pre-render failure.
It may attach CDB only after the ready marker says both `effect_loaded=1` and
`parameters_applied=1`.

An answered return still requires all of the original depth-control evidence:

- project depth is exactly 8bpc;
- one run ID, AE PID, module base, and pinned AEX hash;
- PF8 callback RVA `0x1170870` has a positive hit count; and
- PF32 callback RVA `0x1170c90` has a zero hit count.

This package controls the active callback depth only. It does not classify the
8bpc field/compose algorithm or promote any case to AE exact.
