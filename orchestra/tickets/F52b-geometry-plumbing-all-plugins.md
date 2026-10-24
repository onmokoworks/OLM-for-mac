# F52b: finish realistic-geometry plumbing and measure the other 7 plugins

## Why
- F52 (`orchestra/reports/F52-oracle-downsample-geometry.md`, `next` 1–2) built the oracle options, but the candidate side forwards only downsample, and only Blur, ColorKey and DirectionalBlur were measured.
- Real AE renders black wherever a plugin refuses while the original renders.

## Do
1. **Candidate side.** Add rowbytes padding, extent_hint, request rect, pixel aspect and negotiated output geometry to the source-host wrappers (`tools/fuzz/adapters/`, `harnesses/geometry.hpp`), and to the F47d/F51 bundle host.
2. **Sampler.** Make `--geometry realistic` a tested sampler with replay and shrink support. Defaults stay unchanged, and default replay must be identical.
3. **Measure.**
   - Run seed 1 n100 under `--geometry realistic` for ColorKeep, DistanceGradation, KiraKira, RadialBlur (use its own adapter), ToonDilate, Smoother2, and Smoother (Classic).
   - Report E/M/R/U and the refusal tags. Mark which refusals are faithful (the original errors too) and which are Mac-only.
   - For each plugin that has Mac-only refusals or mismatches, give the first witness and a disassembly pointer to how the original uses downsample.
4. **Re-measure.** Also rerun Blur, ColorKey and DirectionalBlur under the full realistic sampler, padding/extent/aspect included. Report only; P01a/b/c are fixing downsample in parallel.

## Rules
- Use 1-2 processes. Make no plugin source changes.
- Do not change the default worker or the default geometry. Do not touch the release gate or ledger.
- Never edit `04_Tools/AEXCompat*`. The stop rule applies.
