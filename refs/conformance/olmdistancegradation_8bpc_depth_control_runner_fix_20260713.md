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

## Accepted desktop return

The diagnostic v4 returned an accepted same-run control:

- Return SHA-256:
  `5403e85433f93f9bd011589935979721c4e6f124bb04317c577b401ac83e5bc2`
- Run ID: `dglive-983b62b4192243a68411e60f11faab6d`
- AE PID: `5936`
- Module base: `0x7fffcd660000`
- AEX SHA-256:
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- Project depth: 8bpc
- PF8 callback `+0x1170870`: `24377` hits
- PF32 callback `+0x1170c90`: `0` hits

The fail-closed classifier labels this
`pf8_live_pf32_negative_control_exact`. This proves the active 8bpc callback
dispatch and removes the depth-control prerequisite. It does not prove any
pixel value. The next permitted request is the same-run typed boundary at
`(397,281)` for cases `0001`, `0015`, and `0029`.
