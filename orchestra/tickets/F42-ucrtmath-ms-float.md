# F42: UCRT-exact sinf / cosf / log2f (disassembly-guided port, OLM-internal)

## Facts
- `ucrtmath/` (F28) holds AMD-derived `ucrt_expf`/`ucrt_atan2f`/`ucrt_powf`. They are bit-exact
  against ucrtbase 10.0.28000.2705 in both FMA modes.
- F27c/F28 surveys found that sinf/cosf (about 0.8% of inputs) and log2f (about 50%) differ from
  AMD. They are Microsoft's own implementations. The plugins use them: RadialBlur log2f,
  DirectionalBlur sinf/cosf, ColorKey sinf.
- The fuzz oracle still uses host Apple libm for these functions, so the current 0-mismatch results
  at those call sites do NOT prove Windows equality.

## Policy (orchestrator)
- Put the code in `ucrtmath/ms/`, kept separate from the AMD-derived files.
- Mark it as OLM-internal in the README: it is derived from ucrtbase behaviour/disassembly and
  must not be published standalone.
- Never commit Microsoft binaries.

## Do
1. Use the Rosetta oracle (`tools/ucrt_math_probe/rosetta/`) and the disassembly of the pinned
   ucrtbase to implement `ucrt_sinf`, `ucrt_cosf`, `ucrt_log2f`. Cover both FMA modes: argument
   reduction, the polynomial, its coefficients, and the evaluation order including fused ops.
   Then compile natively for arm64 with `-ffp-contract=off` and explicit fma.
2. Run the F28 equivalence harness: all 2^32 inputs × both modes for each function. The result
   must be 0 mismatches. On a mismatch, debug it under the normal stop rule.
3. Do not integrate into the worker or the plugins here. Propose the follow-up: the worker
   import shim (like F30) plus the Mac call sites (like F31).
- Use 1-2 processes. Check `memory_pressure` first.
