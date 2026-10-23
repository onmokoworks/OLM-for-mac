# F47: AEXCompat prototype — run Mac `.plugin` bundles in the same fake AE host as the `.aex`

## Why
- Today the original `.aex` runs in the AEXCompat worker's fake AE host under Unicorn.
- The Mac side does not. The fuzz adapter recompiles the plugin *source* into a separate,
  Python-generated `host.cpp`, arm64 only (`tools/fuzz/adapters/public.py`, `compile_sdk`).
  So we compare the real AEX with a rebuilt Mac port, under two different hosts, and the
  shipped `.plugin` bundle is never tested.
- Goal: load the shipped Mac `.plugin` (Mach-O bundle) natively in the *same* host
  implementation and suites. Then AEX vs `.plugin` is a like-for-like comparison of the
  real binaries.
- The tool belongs to the user, who wants this. Work in a copy; never edit
  `04_Tools/AEXCompat*`.

## Do
1. **Source copy.** Copy the F46 worker source (`~/.cache/olm-emu/src-F46/reference-guest`) to
   `~/.cache/olm-emu/src-F47/`. Study how the guest worker implements the AE host: `PF_InData`,
   the suites (`PF_*Suite`, `AEGP` handles, iterate, world/checkout, smart render pre/post,
   `PF_ABORT`/progress), parameter checkout, and Smart Render. Check whether the existing
   `native_x64` callback path already provides native-ABI callbacks.
2. **Native loader.** Add a `native-plugin` mode to the worker:
   - Load the bundle's executable via `CFBundle`/`dlopen` and resolve `EffectMain` (or the
     PiPL entry point).
   - Read the PiPL from the bundle resource, then build the same InData/suites as the
     emulated path, exposed as native C-ABI function tables backed by the same Rust host
     state.
   - Use the same CLI/session protocol the fuzz adapters already use for the `.aex` worker:
     selectors, params, worlds, Smart route, and output hash.
   - arm64 runs natively. Make x86_64 runnable via `arch -x86_64` with an x86_64 build of the
     worker if that is cheap; otherwise, document it.
3. **Build the `.plugin`s** from the current sources with xcodebuild, Release, Universal, into
   scratch, for at least OLMBlur, ColorKey and RadialBlur. Do not install them into AE.
4. **Fuzz path.** Add an adapter option, `--candidate plugin-bundle <path>`, that runs the
   candidate via the native-plugin worker instead of the recompiled source host. Run seed 1
   n100 for OLMBlur, ColorKey and RadialBlur, AEX vs `.plugin`.
   - Report agreement with the existing source-host results.
   - Every difference is a finding: a host difference, a build or flag difference, or a real
     bug. Classify each one.
5. Put the worker at `~/.cache/olm-emu/worker-F47-nativeplugin/` and add an INDEX entry. Commit
   the patch, the build script and the adapter changes to the OLM repo
   (`tools/emulation/aexcompat_patches/`, `tools/fuzz/`).
   - Do not change the fuzz default candidate.
   - Write a short design note `tools/emulation/aexcompat_patches/F47-native-plugin.md` that
     the user can later upstream.

## Rules
- Use 1-2 processes. Check `memory_pressure` before the Rust build and do not build under 30%
  free. Delete build trees afterwards.
- Do not touch the release gate/ledger, and make no plugin source changes. If a plugin bug is
  found, report it.
- The stop rule applies. Partial progress is valuable; a working loader for one plugin is
  already a success, so report precisely what works.
