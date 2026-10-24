depends: P02i-colorkey-geometry
depends: P02j-directionalblur-geometry
# T15b: random odd/even comp-size sweep, all 10 plugins (resume T15 after its prerequisites)

## State
- T15 (`orchestra/reports/T15-odd-even-random-comp-sweep.md`) qualified the ColorKey/DirectionalBlur hosts for realistic-v1 on the **F52c** oracle (`~/.cache/olm-emu/worker-F52c-geom/`) and found ROI bugs in those two plugins. P02i/P02j fixed them. Now run the sweep the user asked for.

## Do
1. Add an opt-in size sampler (default generation and replay stay identical):
   - width and height drawn independently, odd and even each about 50%, including 1, 2, 3 and primes;
   - sizes from tiny up to the largest the oracle completes inside its 10 s case limit (measure it per plugin and state it);
   - downsample 1/1, 1/2, 1/3, 1/4, 1/8, plus asymmetric; 8/16/32 bpc; aspect 1:1, wide, tall, 1-pixel strips; combined with the realistic-v1 ROI/padding/negotiated-output geometry.
2. Seeds 2026 and 2027, n150 each, all 10 plugins: Smart route (Classic for Smoother v1). Report E/M/R/U per plugin, split odd vs even and by downsample.
3. Classify each mismatch and each Mac-only refusal with its first witness, shrink it, and point to the source line.
   - Fix it only when the cause is a clear, local rounding or size bug in one plugin and the fix keeps the acceptance rule. Otherwise report it with a proposed fix ticket in `next`.
4. Save witnesses into the corpus as a separate labelled set. Standard `tools/fuzz/run.py --replay` (both routes, matching `--geometry`) must report `replay_matches_saved: true`; verify before you finish. Exclude witnesses whose oracle exceeds the 10 s case timeout.

## Acceptance
- Default fuzz: no exact→non-exact. Admitted outputs must be exact. Before/after numbers for any plugin you touched.

## Rules
- Use 1-2 processes. Do not touch the release gate or ledger, never edit `04_Tools/AEXCompat*`, do not rebuild the oracle.
- The stop rule applies; partial per-plugin results are valuable, so finish and report plugins one by one rather than stopping on the first hard case.
