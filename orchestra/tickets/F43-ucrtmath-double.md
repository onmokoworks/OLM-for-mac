# F43: UCRT-exact double sin / cos / exp / pow

## Facts (F28 survey, `orchestra/reports/F28-ucrtmath-lib-amd.md`)
Comparing ucrtbase 10.0.28000.2705 with AMD over 10^8 random inputs:
- sin: about 2.9% differ; cos: about 2.9%; exp: about 0.23%
- pow: only 275 differ, likely the same classes of differences as powf (see F27c/F28)

Plugin users: DistanceGradation (cos/exp/pow/sin), KiraKira (cos/sin), RadialBlur (sin/cos),
ColorKey (sin), Smoother2 (pow), OLMBlur (pow).

## Do
1. **pow.** Start from AMD's double pow and apply general fixes analogous to the powf ones in
   `ucrtmath/` (AMD-derived; it goes in the publishable part).
2. **sin / cos / exp.** Use the same policy as F42 (see its "Policy" and "How to derive"): an
   interoperability reimplementation in `ucrtmath/ms/`, OLM-internal.
3. **Equivalence.** Compare against the Rosetta oracle in both FMA modes: 10^9 random inputs per
   function, plus dense coverage of the plugin argument ranges, the reduction boundaries
   (multiples of pi/2, large arguments), subnormals, and the exp overflow/underflow edges.
   The result must be 0 mismatches.
4. No worker or plugin integration here. Propose the follow-up.
- Use 1-2 processes. Check `memory_pressure` first.
