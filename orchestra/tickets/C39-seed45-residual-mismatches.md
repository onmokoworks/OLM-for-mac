# C39: two admitted Smart mismatches found on fresh seed 45 (DG and RadialBlur)

## Facts (F45 report, `orchestra/reports/F45-integrate-ms-double.md`)
These appear under both the F44 and F45 workers, so they are not math-import related:
- DistanceGradation seed45 case2, PF8. First diff at byte/word 424; 4 words differ; Mac `1a` vs
  ref `19`. The same mismatch was seen on F44's seed44 (case70), so this is a recurring DG
  domain.
- RadialBlur seed45 case8, PF8. First diff at byte 1000; 1 byte differs; Mac `a8` vs ref `e4`.
  The value gap is large. Suspect F41b's relaxed Smart budget admission (merged just before):
  check whether this case was a budget refusal before F41b.

## Do (two plugins, one commit each)
For each case:
1. Reproduce it with the default worker (F46 if merged, else F45).
2. Find the first divergent stage with the existing paired tracers.
3. Fix the general cause. If the fix is not proven, narrow the admission so the domain is
   refused again (mismatch → refusal is acceptable). Say explicitly which of the two you did.
4. Add each case to the plugin's saved corpus as a regression witness.
5. Verify with seed 1 plus seeds 44 and 45, n300 each, for the plugin. Mismatches must be 0 and
   no exact case may be lost. Replay the corpus.
- Use 1-2 processes. Do not touch the release gate/ledger.
