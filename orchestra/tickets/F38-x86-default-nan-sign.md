depends: F37-default-worker-f32

# F38: x86 default-NaN sign in the Mac port (invalid operations)

## Facts
- C24, F31: the remaining OLMBlur Smart mismatches, Blur/1/99 and Blur/31/214, differ only in NaN words.
  Mac gives `0000c07f`, the AEX gives `0000c0ff`, little-endian, so Mac `7fc00000` vs AEX
  `ffc00000`.
- On x86 SSE an invalid operation (inf-inf, 0*inf, 0/0, sqrt(-x)) returns the *default NaN*
  `0xFFC00000`, which has the sign bit set. arm64 returns `0x7FC00000`.
- F29 made the oracle propagate NaN operands in x86 order. This ticket is about *generated*
  NaNs on the Mac side.

## Do
1. Find all residual mismatches whose differing words are only default-NaN sign differences. Use
   the seed 1 and 31 n300 campaigns of all plugins under the current default worker.
2. Design one general mechanism and apply it where the original computes in SSE. Example:
   after the float ops that can raise invalid, canonicalise any freshly generated default NaN
   `0x7FC00000` to `0xFFC00000`, while keeping propagated payloads.
   - Do not rewrite propagated NaNs that the original passes through.
   - Measure its cost on a 4K frame and keep it cheap. A branch-free bit fix on the store path
     is fine.
   - Alternatively, use an arm64 FPCR setting if one exists that matches x86 (check: FPCR.DN
     gives default NaN `0x7FC00000`, which is the wrong sign, so this likely does not work;
     report it).
3. Strict acceptance: no exact → non-exact; the corpora replay. Report the E/M/R/U before and
   after for affected plugins.
- Fix only generically; no per-case patches. Do not touch the release gate/ledger. Use 1-2 processes.
