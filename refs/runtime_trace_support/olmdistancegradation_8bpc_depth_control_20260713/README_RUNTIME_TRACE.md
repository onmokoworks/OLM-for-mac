# OLMDistanceGradation 8bpc Current-AEX Depth Control

Status: runnable depth-control probe. This package does not collect typed
values, coordinates, stage ownership, or algorithm proof. It verifies that AE
actually rendered the requested 8bpc case before interpreting callback hits.

The runner launches AE normally and uses the shared single-case renderer's
pause-before-render handshake. At the ready marker it locates the hash-pinned
`DistanceGradation.aex` module in that AE process, attaches CDB, and arms the
PF8 callback `+0x1170870` and PF32 callback `+0x1170c90` before allowing the
render to continue. It returns one run ID, PID, module base, SHA-256, the
AE-reported project depth, and both hit counts. The required control is PF8 > 0
and PF32 == 0. Do not infer algorithm behavior from it.

If AE does not reach the render-ready marker, the fail-closed return includes
the launcher exit code and stdout/stderr, AE log/result text, target desktop
session, and matching-process diagnostics. Do not resend an unmodified package
after such a failure; use those fields to repair the launch boundary first.

Run `artifacts/run_olmdistancegradation_8bpc_depth_control_20260713.ps1`.
Use `-ParseOnly -TracePath` for the included parser fixtures.
