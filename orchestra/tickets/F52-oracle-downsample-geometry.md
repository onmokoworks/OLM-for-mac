# F52: oracle + fuzzer support for downsample and AE-realistic world geometry

## Why
- Real AE (26.3, measured) renders previews with `in_data->downsample` 1/2 and 1/4, with world sizes 960x540 and 480x270 for a 1920x1080 comp.
- The ported plugins refuse there, and the user sees black. See `orchestra/tickets/P00-ae-realism-refusal-audit.md`.
- Before we fix plugins, the **original AEX behaviour** under downsample and non-trivial geometry must be measurable. The fuzzer currently supports only full frame, origin 0, 1:1 (`tools/fuzz/adapters/public.py:166`).

## Do
1. **Oracle.**
   - In a source copy of the F46 worker (`~/.cache/olm-emu/src-F46/...`, giving `~/.cache/olm-emu/src-F52/`), add session options:
     - `downsample_x/y` (num/den). Set in_data->downsample, and the worlds the host allocates for pre-render/render (`ceil(full*num/den)`).
     - `rowbytes_pad` (extra bytes per row).
     - `extent_hint` / request rect sub-rectangles.
     - `pixel_aspect`.
   - Follow AE SDK semantics, and cite the header lines you rely on.
   - Build to `~/.cache/olm-emu/worker-F52-geom/` and add an INDEX entry.
   - Commit the patch and build script under `tools/emulation/aexcompat_patches/`.
2. **Candidate hosts.** Add the same options to the Mac candidate paths: the source-recompile host in `tools/fuzz/adapters/` and the F47d/F51 bundle host.
3. **Fuzzer.**
   - Add a `--geometry realistic` sampler. Defaults stay unchanged, so existing corpora and seeds replay identically. Run `tools/fuzz` tests, and replay all corpora byte-identically under default options.
   - The sampler draws downsample from {1/1, 1/2, 1/3, 1/4, 1/8, asymmetric}, padding, sub-rect requests, and sizes up to what the oracle can do inside its time limit (state the limit you measured).
4. **Measure.**
   - Run seed 1, n100, for each of the 10 plugins with `--geometry realistic`, oracle F52 vs the current Mac sources, and report E/M/R/U.
   - Classify refusals by tag. Note where the **original** errors or refuses (that is faithful behaviour), and where the original renders but Mac refuses (those are the cases to fix).
   - For a few downsample cases, document how the original actually uses downsample. Check whether it scales radii and by what rounding, citing disassembly addresses. The plugin fix tickets need this.

## Rules
- Use 1-2 processes. Check `memory_pressure` before the Rust build (≥30% free), and delete build trees afterwards.
- Make no plugin source changes. Do not change the fuzz default worker or the default geometry. Do not touch the release gate or ledger.
- Never edit `04_Tools/AEXCompat*`. Build in space-free dirs under `~/.cache/olm-emu/build-F52/`.
- The stop rule applies. Downsample support plus measurements for Blur, ColorKey and DirectionalBlur are already a success.
