# F43c: UCRT-exact double pow (disassembly-guided, OLM-internal)

## Facts
- F43 tried patching AMD's double pow and stopped. The witnesses are in
  `orchestra/reports/F43-ucrtmath-double.md`: W1 is subnormal output rounding, W2 is a normal
  result off by 1 ulp. In 10^8 pairs, 275 (non-FMA) / 267 (FMA) mismatches remain.
- Disassembly-guided reimplementation of UCRT code is approved. Use the F42 policy.

## Do
Stop patching AMD. Understand UCRT's own pow (log/exp table structure, extra-precision path,
rounding of subnormal results) for both FMA modes. Write `ucrt_pow` in `ucrtmath/ms/pow.c`
from your own understanding, with minimal constants and recorded provenance.

Equivalence against the Rosetta oracle, both modes:
- 10^9 random pairs
- plus all F43 witnesses
- plus dense near-1 bases, integer and half-integer exponents, and the overflow/underflow/subnormal
  result boundaries
- plus the plugin ranges: Smoother2/OLMBlur/DG bases in [0, 4] and exponents in [-8, 8]

The result must be 0 mismatches. Use 1-2 processes.
