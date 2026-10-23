depends: F47c-native-plugin-smart-render

# F47d: extend the native `.plugin` bridge to all Smart plugins, plus Smoother v1 Classic

## Facts
F47c (merged): the real arm64 OLMBlur bundle runs SMART_PRE_RENDER/SMART_RENDER through the
shared-arena bridge (`tools/emulation/aexcompat_patches/build_F47c.py`, `--candidate plugin-bundle`).
Seed 1 n100 and orchestrator seed 789 n60 are all exact against the AEX.

## Do
1. Generalise the bridge and adapter to ColorKeep, ColorKey, DirectionalBlur, DistanceGradation,
   KiraKira, Smoother2, ToonDilate and RadialBlur (Smart), and to Smoother v1 (Classic RENDER).
   - Implement only the suites/callbacks each plugin actually uses. Log AcquireSuite during
     render, and make unknown suites fail loudly.
2. Build every bundle in Release, Universal, with `tools/fuzz/build_F47_bundles.py`. R01 added
   Release configs to the real projects, so prefer building the real projects now over
   disposable copies.
3. For each plugin, run seed 1 n100 bundle-vs-AEX and compare with the source-candidate results
   for the same seed. Classify every difference: a bundle or build-flag issue, a bridge issue,
   or a real bug.
4. Also run the **x86_64 slice** for at least OLMBlur under Rosetta with an x86_64 build of the
   worker, if that is cheap. Report it either way.

## Rules
- Use 1-2 processes. Check `memory_pressure` before Rust builds. Do not change the default
  candidate, plugin sources, the release gate or the ledger.
- Report per-plugin status: which plugins work and which are blocked, and why.
