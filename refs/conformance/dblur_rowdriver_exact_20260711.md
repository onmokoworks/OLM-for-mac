# OLMDirectionalBlur rowdriver exact microfixture

This artifact is an AEX/Unicorn execution fixture for `FUN_1800038d0` and its
leaf helpers `FUN_180001000` and `FUN_1800013e0`. The AEX bytes are the oracle;
all recorded outputs are compared by byte equality and SHA-256. No tolerance is
used, and no portable core implementation is claimed.

## ABI facts

- `FUN_1800038d0(start, end, &source, &destination, width, unused, params)`
  uses `RCX`, `RDX`, `R8`, `R9`, then stack arguments 5 through 7.
- `FUN_180001000` has 11 integer/pointer arguments followed by a stack `float`
  coefficient. Its source and destination pixels are four-float RGBA records.
- `FUN_1800013e0` has the same stack-float placement for its coefficient; its
  `char` direction is the third argument and its table/accumulator pointers are
  caller-owned buffers.

## Fixture

`case_0001` is a small non-uniform RGBA fixture. It includes nonzero alpha,
asymmetric RGB values, distinct front/back tables, and nontrivial pre-existing
accumulator values. The generated `manifest.json` records the AEX SHA-256,
instruction count, and SHA-256 for every binary input/output.

Run:

```sh
python3 tools/emulation/test_dblur_rowdriver_exact_20260711.py
```

## FACT / INFERENCE

**FACT:** The ABI and offsets above are taken from the supplied decompilation and
disassembly, and the fixture outputs are direct bytes read after AEX execution.

**INFERENCE:** This fixture is suitable as a portable implementation oracle for
future work, but no portable implementation is included here because exact
equivalence has not been independently proven.
