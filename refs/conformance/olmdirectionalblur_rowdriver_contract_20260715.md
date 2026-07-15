# OLMDirectionalBlur rowdriver contract audit

This is a narrow executable fixture for the forward `FUN_1800013e0` scatter
contract. It uses a 5-wide, 3-row float32 RGBA buffer and places the source at
row 1, column 2. `end == width` permits only two writes, to row 1 columns 3
and 4; a third step would cross the row boundary.

Run:

```sh
python3 tools/emulation/test_dblur_rowdriver_contract_20260715.py
```

**FACT:** The fixture runs the supplied `OLMDirectionalBlur.aex` at
`FUN_1800013e0` (`0x1800013e0`) and compares its raw float32 buffers byte-for-
byte with the current `core/dblur_rowdriver.cpp` export and an explicit model.
The source/weight arrangement gives contributions `0.8 * 0.5` and `0.8 * 0.25`.

**FACT:** The checked model requires width-stride indexing, an exclusive
row-end clamp, denominator addition, and output alpha as the maximum of the
existing value and the contribution. Untouched rows and columns must remain
byte-identical.

**INFERENCE:** This closes only the tested forward scatter leaf contract. It
does not establish rotate ownership, prepass behavior, non-opaque host
writeback, or full-render conformance.
