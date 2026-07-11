# OLMSmoother2 Current-AEX Producer Bytes Return Intake

Date: 2026-07-08

Return archive:

- `refs/returns/windows/20260708_smoother2_current_aex_producer_bytes/20260708_return__olm_runtime_trace_smoother2_current_aex_producer_bytes_20260708_windows.zip`

Local intake artifacts:

- `refs/reports/runtime_trace_summary_smoother2_current_aex_producer_bytes_20260708_20260708_214839.json`
- `refs/reports/runtime_trace_summary_smoother2_current_aex_producer_bytes_20260708_20260708_214839.md`

## Classification

`failed_partial`.

This is not an implementation proof. The archive preserves useful package-local
Mac/Unicorn producer sweeps, but it does not contain the requested same-run
Windows debugger producer-byte/class-plane witnesses.

## Facts Preserved By The Return

For `legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`, the return
preserves local Mac/Unicorn facts:

- `center_b0 = 0`
- `prev_b0 = 1`
- `left_b1 = 0`
- `e170 c = 2`
- `FUN_18000f270` appends locally
- `FUN_18000e3a0` appends locally
- the local no-append three-byte pattern is `center=0, prev=0, left_b1=1,
  c=4`

For `legacy_case_0004_current_aex` at `(1903,519)`, the return preserves local
Mac/Unicorn scanner/class-plane facts:

- no-emit shape 1: `iVar6 >= 4 && iVar5 >= 4`
- no-emit shape 2: `iVar6 >= 2 && iVar5 >= 2 && class_prev_b3 != 0`
- `class_prev_b3` means the left-pixel byte 3 in the local sweep, not byte 0

## Missing Windows Evidence

The contract required a same-run Windows producer witness for at least one
active lane. The return does not provide:

- Windows `0012` `center_b0`, `prev_b0`, `left_b1`, or `e170 c`
- Windows `0012` `f270/e3a0` append facts or cce0 output floats
- Windows `0004` `iVar6`, `iVar5`, `class_prev_b3`, emit/no-emit, polygon
  count, or cce0 output floats

## Decision

Do not change `mac/OLMSmoother2` from this return.

The next useful Windows request must be narrower than the broad producer-byte
package and must force an actual same-run debugger stop on one lane first:

- Prefer `0012 (91,841)` because the local three-byte discriminant is compact.
- Bind the Windows class/byte buffer addresses first, then read
  `center_b0`, `prev_b0`, `left_b1`, and the computed `e170 c` in the same run.
- Only after those bytes are observed should the request continue to
  `f270/e3a0` append/no-append and cce0 output.
