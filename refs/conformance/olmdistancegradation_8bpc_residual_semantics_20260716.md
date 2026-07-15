# OLMDistanceGradation 8bpc Residual Semantics Check

Date: 2026-07-16

## Scope

This is a Mac-only DG tools/emulation result. It does not modify production
image math, package generators, classifier, ledger, or the 2026-07-15 census
return. It does not claim Windows internal values or AE exactness.

The executable harness is
`tools/emulation/test_dg_8bpc_residual_semantics_20260716.py`.

## FACT

- The harness executed the actual `DistanceGradation.aex` callback
  `FUN_181170870` under the repository's AEX emulator for eight field-green
  byte values. Its outputs matched the local model exactly.
- The checked callback path is the retained binary shape: read field green,
  divide by 255, apply `Invert=0` as `1-X`, use Linear interpolation, mix
  configured gradation/background colors, and truncate float results to bytes.
  The callback's memory output is `A,G,R,B`; the census residuals are reported
  in PNG-facing `R,G,B,A` order.
- The harness also ran the existing portable C++ field/packing regression
  through `core/olmdistancegradation_fieldgen.cpp`; it passed.
- Census residual facts are: `case_0001 (17,0)` Mac `[57,0,0,57]` versus
  Windows `[56,0,0,56]`; `case_0015 (780,495)` Mac `[0,0,0,10]` versus
  Windows `[10,0,0,10]`; and `case_0029 (987,496)` Mac `[7,0,60,64]` versus
  Windows `[7,0,63,67]`.

## INFERENCE

- `case_0001` is locally **semantically possible but not proven**: a one-byte
  pre-store/writeback boundary can produce the paired red/alpha `57 -> 56`
  change. The retained census does not provide the residual's field, source,
  pre-store, or store words, so stage ownership is unresolved.
- `case_0015` is **not reproduced locally**. Equal alpha with red-only change
  rules out no stage by itself; field, source/color selection, compose, and
  writeback remain confounded without the requested typed witness.
- `case_0029` is **not reproduced locally**. Red/green remain equal while Mac
  blue and alpha are both three codes lower. That is compatible with a
  field/blur or compose-input difference, but the local facts do not identify
  one, and no Windows internal value is inferred.

## Conclusion

The local lane validates the actual-AEX callback model and the portable core,
but cannot explain all three residuals from retained field/source/compose/
writeback facts. No production tuning is justified. The next discriminating
evidence remains the census-specified typed PF8 chain for the three residuals.
