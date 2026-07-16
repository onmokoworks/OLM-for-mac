# OLMSmoother2 case_0012 second-leaf boundary

Date: 2026-07-16
Status: **Mac actual-AEX / portable exact; Windows continuation unobserved**
AE exact: **false**

## FACT

- The accepted current-case boundary is descriptor `92,841,1,92,842,2`,
  `e170 c=7`, and polygon count `1` after the first `f270 -> e3a0` append.
- Starting from that bound descriptor and first count, checked-in actual AEX
  `FUN_18000df30 -> FUN_18000f130 -> FUN_18000e290` and the portable
  implementation both produce:
  - `df30=0`
  - `f130 -> e290` append `true`
  - returned source coordinate `(92,843)`
  - returned RGBA `(0.125,0.25,0.75,0.625)`
  - returned weight equal to portable within `1e-6`
  - polygon count `1 -> 2`
- The portable and actual-AEX second-leaf predicate, append decision, full
  RGBA payload, weight, and count are equal; the RGBA is deliberately
  distinctive and nonzero.
- Calling the checked-in AEX `FUN_18000fef0` dispatcher with the accepted
  descriptor selects key `0x14` and grows the polygon from `0 -> 2`. The
  portable dispatcher produces the same count.

## Boundary

The accepted live Windows witness ends after the first append at count `1`.
It does not observe the return values of `df30`, `f130`, or `e290`. However,
the accepted descriptor and checked-in current AEX together prove dispatch:
  key `0x14` calls `f270` and then calls `f130` unconditionally. This Mac proof
  closes the checked-in AEX second-leaf payload through `df30 -> f130 -> e290`;
  it does not turn that result into Windows-live or AE-exact evidence.

## Verification

```sh
python3 tools/emulation/test_smoother2_case0012_second_leaf_20260716.py
```

Expected result:

```text
PASS: case0012 second-leaf binding, path, payload, weight, and count contract
accepted descriptor selects fef0 key 0x14; AEX/portable df30->f130->e290 payload and count=2
```

Machine-readable evidence:
`refs/conformance/olmsmoother2_case0012_second_leaf_20260716.json`.

## Claims Not Made

- No live Windows `df30/f130/e290` return values or post-leaf polygon capture.
- No AE-host or AE-exact result.
