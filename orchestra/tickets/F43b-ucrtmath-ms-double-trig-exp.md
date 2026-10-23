# F43b: UCRT-exact double sin / cos / exp (disassembly-guided, OLM-internal)

## Facts
- F42 succeeded with this approach for sinf/cosf/log2f: `ucrtmath/ms/float.c`, all 2^32 inputs
  exact. Read `ucrtmath/ms/README.md` and `orchestra/reports/F42-ucrtmath-ms-float.md`.
- F43 spent its budget on the AMD-patch approach for pow and never started sin/cos/exp.

## Do
Follow F42's policy and "How to derive" in `orchestra/tickets/F42-ucrtmath-ms-float.md`:
- understand the UCRT algorithm (both FMA paths) and write your own C in `ucrtmath/ms/double.c`
- take only minimal constants and record their provenance
- build for arm64 with `-ffp-contract=off` and explicit fma

Implement `ucrt_sin`, `ucrt_cos`, `ucrt_exp`.

Equivalence against the Rosetta oracle in both modes:
- 10^9 random double bit patterns per function
- plus 10^8 within the plugin ranges, |x| <= 64 for sin/cos and [-745, 710] for exp
- plus the reduction boundaries near multiples of pi/2 (large |x| included) and subnormals,
  and the exp overflow/underflow edges

The result must be 0 mismatches. On a mismatch, debug under the normal stop rule. Use 1-2 processes.
