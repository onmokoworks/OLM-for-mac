# OLMSmoother2 case_0012 second-leaf boundary

Date: 2026-07-16
Status: **Mac actual-AEX / portable exact; Windows continuation unobserved**
AE exact: **false**

## FACT

- The accepted current-case boundary is descriptor `92,841,1,92,842,2`,
  `e170 c=7`, and polygon count `1` after the first `f270 -> e3a0` append.
- Starting from that bound descriptor and first count, checked-in actual AEX
  and the portable implementation both produce:
  - `df30=0`
  - `f130 -> e290` append `true`
  - returned source coordinate `(92,843)`
  - polygon count `1 -> 2`
- The portable and actual-AEX second-leaf predicate, append decision, and
  count are equal.

## Boundary

The accepted Windows witness ends after the first append at count `1`. It
does not observe `df30`, `f130`, or `e290`, so this result does not prove that
Windows skips the second leaf. It proves that the local leaf implementation
matches the checked-in AEX for the supplied state and moves the unresolved
boundary to second-leaf dispatch/input ownership before `cce0`.

## Verification

```sh
python3 tools/emulation/test_smoother2_case0012_second_leaf_20260716.py
```

Expected result:

```text
PASS: case0012 second-leaf diagnostic binding and count contract
accepted Windows evidence ends at first count=1; local AEX/portable second leaf count=2
```

Machine-readable evidence:
`refs/conformance/olmsmoother2_case0012_second_leaf_20260716.json`.

## Claims Not Made

- No Windows `df30/f130/e290` internal behavior.
- No claim that Windows skips the second leaf.
- No AE-host or AE-exact result.
