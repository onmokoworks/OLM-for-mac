# F44: integrate ucrt_sinf / ucrt_cosf / ucrt_log2f (worker + Mac + default oracle)

## Facts
- F42, merged: `ucrtmath/ms/` provides `ucrt_sinf`, `ucrt_cosf`, `ucrt_log2f`. They are bit-exact
  against ucrtbase over all 2^32 inputs in both modes. They are OLM-internal.
- The F32 worker (current default) still routes sinf/cosf/log2f to host Apple libm.
- F30 + F31 are the template: F30 built the worker shim, F31 switched the Mac call sites and the default.
- Import users (plugins_2025):
  - sinf/cosf: DirectionalBlur, and sinf in ColorKey
  - log2f: RadialBlur
  - KiraKira, DistanceGradation and RadialBlur use the *double* sin/cos, which are out of scope
    here (F43).

## Do
1. **Worker.** Build an F44 worker from the F32 source with sinf/cosf/log2f routed to `ucrtmath`
   in FMA mode, for both DLL names and both import paths. Put it at
   `~/.cache/olm-emu/worker-F44-msfloat/`, add an INDEX entry, and commit the patch and build
   script to `tools/emulation/aexcompat_patches/`.
   - Validate the shim: 10^6 random inputs per function against the Rosetta oracle, 0
     mismatches.
2. **Mac.** Switch the float-import call sites for sinf/cosf/log2f to `ucrt_*`, matching the
   original import boundary as in F31.
   - Where Mac code evaluates in double and casts while the original imports the float function,
     switch it to the float function.
   - Leave genuine double sin/cos alone.
3. **Default oracle.** Make the F44 worker the default and keep F32 selectable.
4. **Measure.** Run seed 1 plus one fresh seed, n300, on Smart for all plugins, and replay
   every corpus. No exact case may be lost.
   - Rebaseline only saved cases whose reference changed for a demonstrated sinf/cosf/log2f
     reason, and list each one.
   - Report the before/after E/M/R/U.
- Use 1-2 processes. Check `memory_pressure` before the Rust build and do not build under 30% free.
- Do not touch the release gate/ledger.
