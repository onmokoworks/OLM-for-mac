# OLMSmoother2 case0012 unique c280 family oracle

## Verdict

`PASS_ACTUAL_UNIQUE_C280_FAMILIES_WITH_FAIL_CLOSED_AT_FUN_180013630`

Fresh actual c280 produced unique classifier indices `0x00, 0x42, 0x5a, 0xff` from 30 fixtures, with counts `{'0x00': 8, '0x42': 2, '0x5a': 2, '0xff': 18}`.

The `0x00` family matched polygon count, point order, RGBA, and raw IEEE-754 weights for every one of its eight fixtures.

Fail-closed boundary: `FUN_180013630@0x180013630`, the first missing independent raw-weight transform on the `0x42` cardinal path. Families `0x42`, `0x5a`, and `0xff` remain actual-only after that boundary.

No production source or ledger was edited.
