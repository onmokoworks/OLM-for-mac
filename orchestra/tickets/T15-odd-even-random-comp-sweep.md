depends: P01a-blur-downsample
depends: P01b-directionalblur-downsample
depends: P01c-colorkey-downsample
depends: F52b-geometry-plumbing-all-plugins

# T15: random odd/even comp-size sweep, with downsample, for all 10 plugins (user request)

## Why
- The user asked for tests on random comps with odd and even sizes once the downsample fixes have landed.
- Odd sizes combined with downsample are where rounding bugs hide: `ceil(full*ds)` world sizes, odd/even center pixels, half-pixel radii, and row padding. The existing corpora mostly use tiny sizes.

## Do
1. Using the F52 oracle (`~/.cache/olm-emu/worker-F52-geom/`) and the `--geometry realistic` sampler from F52b, add a size sampler:
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
