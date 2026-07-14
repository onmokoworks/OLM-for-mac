# OLMKiraKira Mode 3 Gaussian return: live call/return bound, coefficients absent

Date: 2026-07-14

Return archive:

`refs/windows_returns/20260714/20260714_160633__RETURN__windows_witness_batch_20260714.zip`

## Classification

`answered_partial` at the evidence level, but not an accepted Gaussian
coefficient payload. It must not promote Mode 3 to `AE exact` or change the
production coefficient table.

## FACT

- The live run is one hash-pinned Windows AE Software 32bpc run.
- The AEX identity is `OLMKiraKira.aex`, SHA-256
  `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7`.
- The trace reached `KK_WRAPPER`, `KK_CREATE`, `KK_KERNEL_ENTRY`, and
  `KK_KERNEL_RETURN` under the same run ID.
- The first kernel call reported `ecx=21`, `xmm1=2.5`, and `r8=5`, consistent
  with a 21-tap float32 Gaussian request.
- The return observation reported `raw_bytes=84`, `element=float32`, and a
  return data pointer.
- The required `gaussian_kernel_21_f32_le.bin` artifact is absent from the
  returned archive. No 21 raw words were returned.

## Decision

The call contract and return address are binary-grounded. The coefficient
values remain unproven. Keep the existing OpenCV 4.5.5 sidecar and portable
Gaussian evidence as hypotheses/controls only; do not wire a new production
table from the pointer or from PNG similarity.

## Next evidence required

Repeat the same hash-pinned run with a verified post-return memory dump of
exactly 84 bytes, and include the artifact in the return manifest. Acceptance
requires the 21 little-endian float32 words and an independent comparison to
the pinned OpenCV 4.5.5 oracle.

