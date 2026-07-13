# OLMKiraKira Mode 3/4 Narrowing

Date: 2026-07-12

## Decision

Mode 3 and Mode 4 remain explicitly narrowed to the existing Mode 2
three-box-filter scaffold in the CLI and Mac implementation. This preserves
current behavior and does not claim compatibility for either mode.

## FACT

- The Windows helper dispatch is statically recovered:
  - Mode 3 branches to `FUN_181272ec0`, identified as the OpenCV
    `GaussianBlur` wrapper, at `0x181151100`.
  - Mode 4 falls through to the inline body at
    `0x181150979..0x181150f3a` and makes no subordinate filter call.
- The static audit records Mode 4 factors involving
  `length/(length+1)` and `length/(length+1)^2`.
- The current source previously used three box-filter passes for every mode
  except Mode 1, so Mode 3/4 were already behaviorally equivalent to Mode 2.
- Mode 1/2 are separately grounded as one and three `cv::boxFilter` calls.

Sources: `notes/OLMKiraKira_ASM_FACTS.md`,
`refs/conformance/olmkirakira_mode_dispatch_static_audit_20260710.md`,
`notes/IR_OLMKiraKira.md`.

## INFERENCE / LIMIT

- A faithful Mode 3 port cannot be selected from the recovered target alone:
  the Gaussian wrapper's kernel size, sigma, border, destination depth, and
  exact in-place/alias behavior are not all recovered.
- A faithful Mode 4 port cannot be selected from the two recovered factors:
  the recurrence direction, initialization, pass ordering, edge handling,
  and writeback/normalization sequence are not recovered.
- Therefore implementing a conventional Gaussian or exponential blur here
  would be an inference, not a binary-grounded compatibility change. PNG-only
  tuning is explicitly excluded.

## Code boundary

`BlurModePasses` / `blur_mode_passes` now names this decision in both
`mac/OLMKiraKira/OLMKiraKira.cpp` and `cli/OLMKiraKira/main.cpp`:

- Mode 1: one pass.
- Mode 2: three passes.
- Mode 3/4 and invalid values: three-pass scaffold, pending missing binary
  facts.

The branch changes no rendered output relative to the pre-task code.

## Verification

```sh
python3 refs/scripts/smoke_olmkirakira_mode34_narrowing.py
```

The smoke builds the CLI, checks both source boundaries, and runs the retained
Mode 1/2 dispatch regression. It does not compare PNG appearance or promote
Mode 3/4 to compatibility.
