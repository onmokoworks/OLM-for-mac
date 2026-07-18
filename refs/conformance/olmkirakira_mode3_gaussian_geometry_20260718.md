# OLMKiraKira Mode 3 Gaussian geometry audit (2026-07-18)

Status: **bounded_geometry_shape_proven**
AE exact: **false**
Production edit: **none**

## Bounded result

The recovered Mode 3 call in `FUN_181150790` passes packed size
`0x100000000` (`[0, 1]` in the actual wrapper capture) to
`FUN_181272ec0`, and derives `sigmaX` as `int(length) * 0.5`. Actual-AEX
helper captures for lengths 1, 2, 5, and 9 report that same size and the
expected sigma. A caller-return witness with a 7x9 `CV_32FC1` input returns a
7x9, 63-word float32 output.

This proves the bounded call geometry and observed shape preservation. It does
not prove Gaussian coefficients, border handling, accumulation order, or any
Mode 4 recurrence. No production source was changed.

## Evidence

- Ghidra decomp: `FUN_181150790` calls `FUN_181272ec0` with
  `0x100000000` and `DAT_18148d670`.
- AEX disassembly: `0x1811510d5` loads the constant at `0x18148d670`,
  `0x1811510dd` loads `0x100000000`, and `0x181151100` calls the Gaussian
  wrapper.
- Actual-AEX sweep: `olmkirakira_mode3_sigma_sweep_actual_aex_20260713.json`.
- Actual-AEX return: `olmkirakira_mode3_gaussian_output_actual_aex_20260713.json`.

## Re-run

`python3 tools/emulation/audit_olmkirakira_mode3_gaussian_geometry_20260718.py`

`python3 tools/emulation/test_olmkirakira_mode3_gaussian_geometry_20260718.py`
