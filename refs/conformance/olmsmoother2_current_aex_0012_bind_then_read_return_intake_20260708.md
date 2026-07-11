# OLMSmoother2 Current-AEX 0012 Bind-Then-Read Return Intake

Date: 2026-07-08

Return archive:

- `refs/returns/windows/20260708_smoother2_0012_bind_then_read_failed_partial/20260708_return__olm_runtime_trace_smoother2_current_aex_0012_bind_then_read_20260708_windows.zip`

Local intake command:

- `python3 scripts/intake_olm_return.py /Volumes/onmk/olm_pr/new/20260708_return__olm_runtime_trace_smoother2_current_aex_0012_bind_then_read_20260708_windows.zip --runtime-summary-json refs/reports/runtime_trace_summary.json --runtime-summary-md refs/reports/runtime_trace_summary.md`

## Classification

`failed_partial`.

This is not an implementation proof. The return correctly preserves the
`0012`-only bind-then-read request shape, but it still does not contain a fresh
same-run Windows Stage A bind or Stage B typed byte read for witness `(91,841)`.

## Facts Preserved By The Return

For `legacy_case_0012_gamma5_red_blue_current_aex` at `(91,841)`, the return
preserves package-local Mac/Unicorn facts:

- `center_b0 = 0`
- `prev_b0 = 1`
- `left_b1 = 0`
- `FUN_18000e170` bitsum `c = 2`
- `FUN_18000f270`: append locally
- `FUN_18000e3a0`: append locally
- local suppressing family: `center_b0 = 0`, `prev_b0 = 0`, `left_b1 = 1`,
  `c = 4`

## Missing Windows Evidence

The return does not provide:

- Windows Stage A module base from a witness-local stop
- Windows Stage A exact hook/breakpoint site
- Windows Stage A exact `case_id` and `(91,841)` xy binding
- concrete Windows pointer/address arithmetic for `center_b0`, `prev_b0`, and
  `left_b1`
- same-run Windows `center_b0`, `prev_b0`, `left_b1`, or observed `e170 c`

## Decision

Do not change `mac/OLMSmoother2` from this return.

The next useful retry is still Windows-side and should stay `0012`-only, but it
should optimize even harder for Stage A first: bind the exact witness-local stop
and return the module base, hook site, bound xy, and concrete pointer recovery
route. Stage B byte reads only become meaningful after that bind exists in the
same run.
