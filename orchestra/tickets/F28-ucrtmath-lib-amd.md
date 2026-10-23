# F28: `ucrtmath` — bit-exact UCRT math on arm64 Mac, AMD-derived functions first

## Background (facts; F27/F27b/F27c are merged, read `orchestra/reports/F27c-ucrt-math-exhaustive.md`)
- Oracle: the Rosetta PE loader in `tools/ucrt_math_probe/rosetta/` runs ucrtbase
  10.0.28000.2705 in both FMA modes. It is qualified against Unicorn and MPFR.
- expf: UCRT and AMD aocl-libm-ose agree over all 2^32 inputs, mode for mode
  (UCRT non-FMA = AMD contraction-off; UCRT FMA = AMD FMA). The one exception is signaling
  NaNs: UCRT quiets them, while AMD returns x. Between the two UCRT modes exactly one finite
  input differs (c2890f89).
- atan2f: in 10^8 random pairs, 1594 mismatches are NaN operand priority/payload and there is
  one finite subnormal case: 803c1252/0686decf → UCRT b8e40bc6, AMD b8e40bc5.
- powf: 1727 mismatches per 10^8 pairs, from three diagnosed causes: rounded vs truncated log
  table index, the underflow cutoff, and the NaN sign under an odd exponent.
- sinf/cosf: different implementations; about 0.8% of inputs differ from AMD. Not in this ticket.
- Transcendental imports of the plugins_2025 AEXes (`objdump -p`):
  - float: expf, powf, atan2f, sinf, cosf, log2f
  - double: sin, cos, exp, pow
  - ceil/floor/sqrt/fmod/nextafter are exact by IEEE, so they need no work.

## Goal
Create a standalone C library `ucrtmath/` at the repo root. It must not include anything from
OLM plugin code, because it may become its own repo later.
- Provide `ucrt_expf`, `ucrt_atan2f`, `ucrt_powf`, each with an explicit mode: `UCRT_FMA` or
  `UCRT_NOFMA`.
- Each must be bit-exact with the oracle for its mode, compiled **natively for arm64** by Apple
  clang.
- Start from the AMD BSD-3 sources. Keep their license header and add a NOTICE file. Make the
  smallest general changes the F27c diagnosis calls for: sNaN quieting for expf; the three
  powf causes; the atan2f subnormal and NaN-priority paths.
- No per-input tables of expected outputs.

## Steps
1. Vendor only the needed AMD scalar C files and tables, pinned to commit `29fd054f`.
   - Build for arm64 with `-ffp-contract=off`.
   - The FMA mode must use explicit `fma()`/`fmaf()` exactly where UCRT/AMD-FMA fuses. Find
     those places from the AMD source and verify them against the UCRT FMA disassembly.
   - Never rely on compiler contraction.
2. **Equivalence harness.** Feed the same inputs to the arm64 library and to the x86_64
   Rosetta oracle, for example via files or pipes in chunks, and compare raw bits.
   - expf: all 2^32 inputs × both modes.
   - atan2f/powf: 10^8 random pairs × both modes, plus the F27c witnesses and the paper's
     worst-case inputs.
   - Add targeted sets: near 1, subnormals, the underflow/overflow boundaries, and integer and
     half-integer exponents for powf.
   - Report the mismatch count, which must be 0. If it is not 0, report and stop as `partial`.
   Use 1 process, 2 at most. Check `memory_pressure` before you start.
3. **Survey the remaining imports with no library code yet.** Use the same F27c sweep machinery
   on log2f (all 2^32) and on double sin/cos/exp/pow (10^8 random, plus the ranges the plugins
   use). Compare UCRT, AMD, and Apple for each. Record which ones AMD matches.
4. **Report** per-function results and a recommendation for which functions need a
   disassembly-guided port (sinf/cosf at least).

## Rules
- No plugin, AEXCompat, or fuzzer-oracle changes. Integration comes in the next ticket.
- Never commit Microsoft binaries or code derived from disassembling them. This ticket is
  AMD-derived only; for UCRT, observe its behaviour, do not copy its code.
- Keep committed results under 5 MB. Stop rule applies.
