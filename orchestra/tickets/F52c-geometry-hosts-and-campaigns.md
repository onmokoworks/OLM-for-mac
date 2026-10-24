# F52c: geometry plumbing on both hosts + 7-plugin realistic campaigns (F52b continuation, authorized)

## State
- F52 built the oracle `~/.cache/olm-emu/worker-F52-geom/` with options for downsample, rowbytes pad, extent hint, request rect and pixel aspect.
- F52b added the versioned `--geometry realistic` sampler with replay/shrink. It rejects every adapter until a candidate host qualifies. F52b stopped because:
  - the oracle doesn't negotiate expanded output allocation;
  - it believed rebuilding a reference worker needed authorization.
- Read `orchestra/reports/F52-oracle-downsample-geometry.md`, `F52b-geometry-plumbing-all-plugins.md` and `P01a-blur-downsample.md`. P01a fixed Blur; P01b and P01c are in flight.

## Authorization
- **You are authorized to build a new reference worker** `~/.cache/olm-emu/worker-F52c-geom/` from a source copy (`~/.cache/olm-emu/src-F52c/`, starting from src-F52). Add an INDEX entry, and commit the patch and build script under `tools/emulation/aexcompat_patches/`.
- Do not change the default worker. Build in space-free dirs, check `memory_pressure` (≥30%) and use one job.

## Do
1. **Oracle.** Add negotiated output allocation: honour the plugin's PreRender `result_rect` / `max_result_rect` when it is larger than the input, the way AE does (output world sized to the result rect, with origin offsets). Cite the SDK. Requalify against F52: default geometry must be byte-identical.
2. **Candidate source host.** Implement the same options in `tools/fuzz/adapters/` and `harnesses/geometry.hpp`: padding, extent, request rect, aspect and negotiated output. Qualify each adapter so `--geometry realistic` enables it.
3. **Bundle host.** Add the same to the F47d/F51 bundle host, so the shipped `.plugin` can be run under realistic geometry. This one is lower priority; do it after 4 if time is short.
4. **Measure.**
   - Run seed 1 n100 `--geometry realistic` for ColorKeep, DistanceGradation, KiraKira, RadialBlur, ToonDilate, Smoother2, Smoother (Classic) and Blur. Report E/M/R/U and the refusal tags.
   - Mark each refusal faithful (the original errors too) or Mac-only, and give the first witness plus a disassembly pointer for how the original uses downsample and the other geometry.
   - DirectionalBlur and ColorKey are being fixed in parallel; measure them only if P01b/P01c have already merged on main.
5. Propose a fix ticket per plugin in `next`.

## Rules
- Use 1-2 processes. Make no plugin source changes. Do not touch the release gate or ledger.
- Never edit `04_Tools/AEXCompat*`. The stop rule applies.
