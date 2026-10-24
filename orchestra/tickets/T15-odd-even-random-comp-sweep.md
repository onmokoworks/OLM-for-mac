depends: P02a-colorkeep-geometry
depends: P02b-distancegradation-geometry
depends: P02c-kirakira-geometry
depends: P02d-radialblur-geometry
depends: P02e-toondilate-geometry
depends: P02f-smoother2-geometry
depends: P02g-smoother-geometry
depends: P02h-blur-geometry
# T15: random odd/even comp-size sweep, with downsample, for all 10 plugins (user request)

## Why
- The user asked for tests on random comps with odd and even sizes once the downsample fixes have landed.
- Odd sizes combined with downsample are where rounding bugs hide: `ceil(full*ds)` world sizes, odd/even center pixels, half-pixel radii, and row padding. The existing corpora mostly use tiny sizes.

## Do
0. **Prerequisite (found by the first T15 attempt, see `orchestra/reports/T15-odd-even-random-comp-sweep.md` on branch history aca96437).**
   - Use the **F52c** oracle `~/.cache/olm-emu/worker-F52c-geom/`, NOT F52. F52 rejects `--negotiate-output` with usage code 2. See `orchestra/reports/F52c-*.md` for how P02a-h invoked it.
   - The ColorKey and DirectionalBlur source hosts do not yet declare realistic-v1 (`tools/fuzz/geometry.py:67`). Qualify them the way F52b/F52c qualified the other eight: plumbing, a negotiated-output check, and a short realistic run.
   - If that reveals Mac-only refusals or mismatches in those two plugins, fix them under the same acceptance as P02 (contract route exact, 0 Mac-only refusals).
1. Using that oracle and the `--geometry realistic` sampler, add a size sampler:
   - width and height drawn independently, with odd and even each about 50%, including 1, 2, 3 and primes;
   - sizes from tiny up to the largest the oracle completes within its time limit (measure it; F52 measured Blur 1920x1080 at 1/2 in about 5 s);
   - downsample 1/1, 1/2, 1/3, 1/4, 1/8, plus asymmetric;
   - 8/16/32 bpc;
   - aspect: 1:1, wide, tall, and 1-pixel strips.
2. Run two fresh seeds per plugin (2026, 2027), n150 each, across all 10 plugins: Smart route, and Classic for Smoother v1. Report E/M/R/U per plugin, split odd vs even and by downsample.
3. Classify each mismatch and each Mac-only refusal with its first witness, give a minimal repro (shrink it), and point to the source line.
   - Fix it only when the cause is a clear, local rounding or size bug in one plugin and the fix keeps the acceptance rule. Otherwise report it.
4. Save the witnesses into the corpus in a separate labelled set, and keep default replay identical.

## Acceptance
- Default fuzz: no exact→non-exact. Admitted outputs must be exact.
- Report before/after numbers for any plugin you touched.

## Rules
- Use 1-2 processes. Do not touch the release gate or ledger, and never edit `04_Tools/AEXCompat*`.
- The stop rule applies.

- Save corpus witnesses so that standard `tools/fuzz/run.py --replay` (both routes, the matching `--geometry`) reports `replay_matches_saved: true`, and verify that before you finish. Exclude witnesses whose oracle exceeds the 10 s case timeout.
