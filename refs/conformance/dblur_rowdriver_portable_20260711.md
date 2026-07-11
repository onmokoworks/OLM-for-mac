# OLMDirectionalBlur portable rowdriver candidate

Status: **portable-candidate-byte-exact-bounded**.

`core/dblur_rowdriver.cpp` now contains typed C ABI candidates for the two
decompiled leaf functions and a one-call default-mode `FUN_1800038d0`
candidate.
The rowdriver ABI makes the required buffers, coefficient fields, tables,
counts, and comp-map explicit instead of passing the opaque 0x8200-byte host
params block.

## Exact gate

Run:

```sh
python3 tools/emulation/test_dblur_rowdriver_portable_20260711.py --write-fixtures
python3 tools/emulation/smoke_dblur_rowdriver_portable_20260711.py
```

The fixture set contains five valid, three-row actual-AEX leaf cases varying
width, coefficient, alpha-zero behavior, direction, boundaries, and
pre-existing accumulators. Comparison is byte equality only, and all five cases
pass. The second leaf argument is a row base (`row * width`); an earlier
one-row fixture with an arbitrary offset caused out-of-bounds oracle writes and
was invalidated.
The candidate gate uses `-O2 -fno-fast-math -ffp-contract=off`.

## FACT / INFERENCE

**FACT:** `FUN_1800038d0` passes the fields represented by the typed rowdriver
ABI to `FUN_180001000` and `FUN_1800013e0`; the mapping is from the supplied
decompilation offsets `0x20`, `0x2c`, `0x30`, `0x38`, `0x40`, `0x44`,
`0x48..0x54`, `0x58`, `0x4068`, `0x3ed8`, `0x7ee8`, `0x8080`, `0x8088`,
`0x8118`.

**FACT:** The actual-AEX leaf fixture gate is 5/5 byte-exact, including
destination, denominator, valid/alpha, and guarded boundaries. No tolerance is
used.

**INFERENCE:** The exported typed rowdriver shape is a viable detour boundary;
the separate full-rowdriver gate supplies the complete-function evidence.
