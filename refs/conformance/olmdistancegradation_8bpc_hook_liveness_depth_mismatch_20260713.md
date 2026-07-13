# OLMDistanceGradation 8bpc hook-liveness depth mismatch

Date: 2026-07-13

## Classification

The returned hook-liveness request is a contract-valid `answered` result, but
it is not 8bpc liveness or algorithm proof. All five requested RVA hit counts
are zero because the AE run reported `project_bits_per_channel: 32` while the
request contract selected `comp.bpc: 8`.

## FACT

- Return SHA-256:
  `85f7655d56cd8e2eeec46f0ea6fc4e6a25c2ee9d2355a2f5cb2a8d856aede38e`.
- AEX SHA-256:
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- AE rendered `case_0001` successfully at 32bpc.
- CDB loaded the expected module and accepted all five breakpoints.
- `+0x1170870` is the PF8 callback. `+0x1170c90` is the PF32 callback.
- The four `+0x11705xx/+0x11708xx` interior hooks are PF16-only.
- The stale packaged renderer read only `project.bits_per_channel`; the request
  stores its depth in `comp.bpc`. The current shared renderer supports both.

## Decision

Do not retry the five mixed-depth hooks. The replacement depth-control request
requires the AE result to report 8bpc, arms only PF8 `+0x1170870`, and arms
PF32 `+0x1170c90` as a negative control. The expected result is PF8 greater
than zero and PF32 equal to zero. Any different observed counts remain depth
dispatch evidence only and must not be used for pixel tuning.

Package:
`refs/runtime_trace_packages/olm_runtime_trace_olmdistancegradation_8bpc_depth_control_20260713.zip`
