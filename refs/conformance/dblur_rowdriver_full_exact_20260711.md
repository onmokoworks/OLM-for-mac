# OLMDirectionalBlur full rowdriver conformance gate

Status: **portable-candidate-byte-exact-bounded**.

The gate runs `FUN_1800038d0` from `plugins_2025/OLMDirectionalBlur.aex` on
three bounded planes with 3, 4, and 5 rows. The rowdriver receives row ranges,
and its leaf calls receive `row * width` offsets. The cases use widths 5, 7,
and 9; zero and nonzero source alpha; distinct front/back weights and counts;
exponent, divisor, edge factors; pre-existing destination/denominator/alpha;
and varying component-map area, row position, and extent. The third case uses
`mode=1` (`params +0x20 = 1`), while mode 2 and mode 3 are outside this gate.

The params block writes the four inline tables at `+0x58`, `+0x3ed8`,
`+0x4068`, and `+0x7ee8`. It writes pointers at `+0x8080`, `+0x8088`, and
`+0x8118`. Actual AEX destination, denominator, and alpha output bytes are
stored under `replay/fixtures/dblur_rowdriver_full/*/actual_*.bin`.

## Exact policy

Comparison is byte equality only. No tolerance is used. Every guarded input and
output buffer has prefix and suffix canaries; all three cases passed the canary
check.

All three rowdriver fixtures match the actual AEX byte-for-byte for destination,
denominator, and alpha buffers. The actual-AEX harness registers `powf`; an
earlier run without that import returned zero by loader policy and was
invalidated before this status was assigned.
The candidate is compiled with `-O2 -fno-fast-math -ffp-contract=off`; this
exact build is also used by the full-render detour.

The complete machine-readable result is in
`refs/conformance/dblur_rowdriver_full_exact_20260711.json`.

## Commands

```sh
python3 tools/emulation/test_dblur_rowdriver_full_exact_20260711.py --write-fixtures
python3 tools/emulation/smoke_dblur_rowdriver_full_exact_20260711.py
```

## FACT / INFERENCE

**FACT:** `FUN_1800038d0` is called with row start/end and passes a flat
`row * width` base to the leaf helpers, as observed in the supplied
decompilation and exercised by these 3+ row planes.

**FACT:** The actual AEX outputs were read after full rowdriver execution and
compared byte-for-byte with the candidate outputs.

**FACT:** The mode=1 case, all three canary checks, and all complete-buffer byte
comparisons passed.

**INFERENCE:** This bounded gate is sufficient to use the candidate as a
full-render emulation detour. It is not by itself Mac AE exact evidence.
