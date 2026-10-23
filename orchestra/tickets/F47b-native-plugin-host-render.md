depends: F47-aexcompat-native-plugin-host

# F47b: native `.plugin` host — implement the selectors and suites needed to render OLMBlur

## Facts
F47, merged and partial (`orchestra/reports/F47-aexcompat-native-plugin-host.md`,
`tools/emulation/aexcompat_patches/F47-native-plugin.md`): the F47 worker at
`~/.cache/olm-emu/src-F47` loads Universal bundles and resolves the PiPL EffectMain on arm64.
Native selectors, suite callbacks and rendering do not exist yet.

## Do (scope: make ONE plugin, OLMBlur, render end-to-end; then generalise if time allows)
1. Expose the worker's existing Rust host state as native C-ABI tables: PF_InData, PF_OutData,
   the param defs, PF_EffectWorld, the interact/utility callbacks, and the suites OLMBlur
   acquires. Log the actual `AcquireSuite` calls to find out which ones.
   - Reuse the emulated path's semantics exactly. Prefer a thin shim over reimplementation.
2. Support GLOBAL_SETUP, PARAMS_SETUP, SEQUENCE_SETUP, then SMART_PRE_RENDER / SMART_RENDER,
   with the same session protocol the fuzz adapter uses for the `.aex` worker.
3. Add the adapter option `--candidate plugin-bundle <path>` in `tools/fuzz/` and run OLMBlur
   seed 1 n100, AEX vs `.plugin`, in the same host. Compare with the existing source-host
   results and classify every difference.
4. Then do ColorKey and RadialBlur if feasible.

## Rules
- Use 1-2 processes. Check `memory_pressure` before the Rust build. Delete build trees.
- Do not change the default candidate. Make no plugin source changes, and do not touch the
  release gate/ledger.
- Partial progress counts. Report precisely which selectors and suites work.
