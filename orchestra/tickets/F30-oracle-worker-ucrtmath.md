depends: F29-unicorn-sse-nan-propagation

# F30: reference worker with UCRT-exact expf/atan2f/powf (+ F29 NaN fix)

## Background (facts)
- F28, merged: `ucrtmath/` provides `ucrt_expf`, `ucrt_atan2f`, `ucrt_powf` with an explicit
  mode (FMA / non-FMA). On native arm64 they are bit-exact against ucrtbase 10.0.28000.2705:
  expf over all 2^32 inputs, atan2f/powf over 10^8 pairs, both modes.
- The AEXCompat worker currently substitutes host Rust/Apple libm for these imports
  (`guest/crates/aex-guest-worker/src/x64/imports.rs` and `native_x64/imports.rs`:
  `install_float_import(... f32::exp)` etc.). The oracle is therefore wrong at these call sites.
  C17, C18, C21, C24, C25 and C26 all deferred their `ucrt-math` clusters to this point.
- ColorKey: 25 uncompared cases come from the worker rejecting
  `api-ms-win-crt-math-l1-1-0.dll!atan2f` (C20).
- F29, merged before this ticket starts: built a worker variant with x86 SSE NaN propagation
  fixed, with its patch and build script under `tools/emulation/aexcompat_patches/`.

## Goal
Build one new reference worker variant: F29's NaN fix plus the expf, atan2f and powf imports
routed to `ucrtmath` in **FMA mode**. Every x64 CPU since 2013 has FMA3, and UCRT enables
FMA3 at startup on such CPUs. Make the mode a worker option or env (`OLM_UCRT_FMA=0|1`,
default 1).
Do not route other math imports. Leave log2f, sinf, cosf and the double sin/cos/exp/pow exactly
as they are now, and list them in the report as still host-math.

## Steps
1. Start from F29's patched source copy, or re-apply its patch onto a fresh copy in
   `~/.cache/olm-emu/src-F30/`.
   - Link `ucrtmath` into the worker: a C static lib through a build.rs/cc step, or a
     Rust FFI to a prebuilt `.a`.
   - Route `expf`/`atan2f`/`powf` for both `api-ms-win-crt-math-l1-1-0.dll` and
     `ucrtbase.dll`, in both the legacy and native_x64 import paths.
   - Build to `~/.cache/olm-emu/worker-F30-ucrtmath/` and add an INDEX.json entry.
   - Commit the patch and build script to `tools/emulation/aexcompat_patches/`.
2. Validate the import shim alone. Drive the worker's imported expf/atan2f/powf through a tiny
   guest call path or the existing unit-test hooks with 10^6 random inputs each. Compare raw
   bits against the F27 Rosetta oracle in FMA mode. Mismatches must be 0.
3. Re-measure. Use the new worker with `--worker` in `tools/fuzz/run.py`. Do not change the
   default.
   - Run seed 1 n300 Smart for every plugin.
   - Replay every corpus.
   - Report per plugin which saved/campaign results change, and why: expf/atan2f/powf or NaN.
   - Any exact → non-exact change must be explained by one of those two causes, or it is a
     finding.
4. In `next`, propose the default-worker switch and corpus rebaseline as a separate ticket. Add
   the list of Mac-port call sites that must switch to `ucrt_*` to become exact under the new
   oracle (grep `expf(`/`powf(`/`atan2f(`/`std::exp` in `mac/` and `core/`).

## Rules
- Use 1-2 processes. Check `memory_pressure` before the Rust release build and do not build
  under 30% free.
- Delete build trees afterwards; keep the binary.
- No plugin code changes. No change to the default worker or the corpora.
