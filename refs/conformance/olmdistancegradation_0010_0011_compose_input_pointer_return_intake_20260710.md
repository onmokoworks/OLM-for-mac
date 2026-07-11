# OLMDistanceGradation 0010/0011 Compose Input Pointer Return Intake

Date: 2026-07-10

Return zip:
`refs/returns/windows/20260710_distancegradation_0010_0011_compose_input_pointer_partial/20260710_003842__olmdistancegradation_0010_0011_compose_input_pointer_partial_windows.zip`

Request:
`olmdistancegradation_0010_0011_compose_input_pointer_witness_20260709`

Status: `partial_compose_inputs_bound_not_exact_xy`

## Result

This return is a useful partial. It confirms the static correction for
`FUN_181170480`: the field-world input is read through `RCX`, while the late
`RDX` path is source/shade input. It does not yet bind the exact residual
pixels `(6,40)` and `(901,394)`.

Confirmed sites:

- `DistanceGradation+0x117057d`: `RCX` field-world read.
- `DistanceGradation+0x11705f1`: `RDX` source/shade read.
- `DistanceGradation+0x1170814`: final writer still sees the source/shade
  side in `RDX`; this must not be treated as field-world proof.

Retained broad `x=6` examples from the return:

- Field read:
  - `rcx=0000021d8e792930`
  - words: `1804 1804 1804 1804 1568 1568 1568 1568`
  - `xmm1=32768`
  - `xmm2=0.792847`
- Source/shade read:
  - `rdx=0000021d8d7b2930`
  - words: `0000 0000 0000 0000 0000 0000 0000 0000`
  - `xmm1=0.187622`
  - `xmm2=0.812378`
- Final writer:
  - site: `DistanceGradation+0x1170814`
  - `rdx=0000021d8d7b2930`
  - `rdi=0000021d8e792930`
  - `xmm2=0.812378`
  - `xmm6=26620`

## Exact XY Attempt

The Windows run also tried a stricter gate:

- gate: `r9=x and rbp=y`
- `(6,40)`: no exact hit
- `(901,394)`: no exact hit

Conclusion: `rbp` is not a reliable y-coordinate discriminator at these compose
sites in this run shape.

## Acceptance

Accepted as partial evidence only.

This return proves:

- `RCX`/`RDX` roles at compose input.
- The old `rdx producer` request was semantically misclassified.
- A naive `r9=x && rbp=y` gate should not be repeated.

It does not prove:

- exact same-run `RCX` field words for `(6,40)` or `(901,394)`;
- exact same-run `RDX` source words for `(6,40)` or `(901,394)`;
- field producer or field pack-site for either target pixel.

## Next Allowed Action

Create a narrowed exact-address witness. The next Windows request must derive
the row/pixel discriminator from pointer address math, not from `rbp=y`.

The useful proof shape is:

- derive or record field/source/output base pointers, rowbytes, pixel size, and
  channel layout for the active 16bpc case;
- compute target addresses for `(6,40)` and `(901,394)`;
- gate `+0x117057d`, `+0x11705f1`, and final writer sites by address equality
  or a proven address range;
- capture same-run `RCX` field words, `RDX` source words, compose scalars, and
  final store words for the exact pixels.

## Forbidden Followups

- Do not resend the same compose-input package unchanged.
- Do not use `rbp=y` as the exact y gate.
- Do not treat broad `x=6` examples as exact `(6,40)` proof.
- Do not tune the Mac implementation from this partial evidence alone.
