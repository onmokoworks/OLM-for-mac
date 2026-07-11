# OLMSmoother2 current-AEX producer-byte witness contract

Date: 2026-07-08

## Purpose

Resolve the remaining `OLMSmoother2` legacy/current-AEX residuals by proving
the first producer divergence upstream of the already-grounded final writer.

This request is intentionally not a final-writer request. Final writer bytes and
writer-frame floats are already strong enough to rule out PNG/export packing as
the active blocker.

## Required cases

Use the current Windows AE Software current-AEX recapture:

- `legacy_case_0012_gamma5_red_blue_current_aex`
- `legacy_case_0004_current_aex`

## Witnesses

### case 0012

Target pixel: `(91,841)`

Local Mac AEX/Unicorn producer sweep:

- local bytes: `center=0`, `prev=1`, `left_b1=0`
- local `e170 c`: `2`
- local behavior: append survives through `f270/e3a0`
- only local three-byte no-append pattern: `center=0`, `prev=0`,
  `left_b1=1`, `c=4`

Windows must return, from the same run:

- `center_b0`
- `prev_b0`
- `left_b1`
- `e170 c`
- `FUN_18000f270` append/no-append
- `FUN_18000e3a0` append/no-append and weight/source if it appends
- cce0 output floats before final u8 packing

### case 0004

Target pixel: `(1903,519)`

Local Mac AEX/Unicorn producer sweep:

- no-emit shape 1: `iVar6 >= 4 && iVar5 >= 4`
- no-emit shape 2: `iVar6 >= 2 && iVar5 >= 2 && class_prev_b3 != 0`
- `class_prev_b3` means left-pixel byte 3, not byte 0

Windows must return, from the same run:

- `iVar6` right scanner span
- `iVar5` down scanner span
- `class_prev_b3`
- emit/no-emit guard result
- polygon vertex count before `bb10/b120`
- cce0 output floats before final u8 packing

## Acceptance

`answered` requires typed same-run producer facts for at least one of the two
active lanes:

- for `0012`, the three producer bytes plus `e170 c` and append/no-append
  facts; or
- for `0004`, scanner spans, `class_prev_b3`, emit/no-emit, polygon count, and
  cce0 output.

`answered_partial` is acceptable only when the failed hook/breakpoint reason is
precise enough to design the next narrower attempt.

Final writer bytes alone, broad breakpoint hit counts, old writer-frame facts,
or broad PNG rerenders are not sufficient.

## Local evidence

- `refs/conformance/olmsmoother2_producer_branch_sweep_20260708.md`
- `refs/conformance/olmsmoother2_producer_branch_sweep_20260708.json`
- `tools/emulation/SMOOTHER2_PRODUCER_EMU_REPORT.md`
