# F53: oracle and candidate hosts: input checkout smaller than the layer (cropped checkout)

## Why
- In real AE, a Smart plugin's input checkout covers only the requested region (`PF_CheckoutResult.result_rect`). Its world can therefore be smaller than `ceil(layer × downsample)` and offset from the layer origin. This happens when a comp is zoomed, partially visible, or a downstream effect asks for a sub-rect.
- P00b's real-bundle audit (situation "cropped-expand") shows two cases:
  - DirectionalBlur refuses at `SmartRender:smart-generic-world-or-budget@2710`;
  - Smoother2's PreRender produces an unequal world pair.
- P04b could not get an original witness: F52c's `Geometry::world()` derives the input world only from layer × downsample, and `resident.rs` rejects a smaller payload (`resident input slot has 1200 bytes, expected 4800`). See `orchestra/reports/P04b-directionalblur-cropped-checkout.md` and `P04b-evidence/oracle-geometry-excerpts.txt`.

## Do
1. **Oracle.**
   - In a source copy of F52c (`~/.cache/olm-emu/src-F52c/`, giving `src-F53/`), add an independent **checkout rect** option: the input world is that sub-rect of the (downsampled) layer, with world dimensions taken from the rect. Follow AE semantics for `PF_CheckoutResult.result_rect` and `max_result_rect`, and for what the plugin sees in `PF_SmartRenderExtra` input worlds. Cite the SDK header lines you rely on.
   - The checkout rect must come from (a) an explicit option and (b) by default, the intersection of the plugin's PreRender checkout request with the layer, as AE does.
   - Keep all existing options byte-identical when the new option is absent.
   - Build to `~/.cache/olm-emu/worker-F53-geom/`, add an INDEX entry, and commit the patch and build script under `tools/emulation/aexcompat_patches/`.
2. **Candidate hosts.** Add the same option to the source and bundle candidate hosts.
3. **Sampler.** Add an opt-in `realistic-v2` geometry (realistic-v1 plus cropped checkout). Default and realistic-v1 generation and replay must stay identical.
4. **Measure.** Run seed 1, n100, realistic-v2, for all 10 plugins. Report E/M/R/U and refusal tags, and separate original refusals from Mac-only refusals. Include the P04b 40x30/20x15 DirectionalBlur witness, and a Smoother2 cropped witness that records the original PreRender result_rect.

## Rules
- Use 1-2 processes. Check `memory_pressure` (≥30% free) before the Rust build, and delete build trees afterwards.
- Never edit `04_Tools/AEXCompat*`; build in space-free dirs under `~/.cache/olm-emu/build-F53/`.
- Make no plugin source changes. Do not touch the release gate or ledger. Do not change the default fuzz worker.
- Commit partial results at least every 30 minutes. The stop rule applies. Getting the oracle to accept cropped checkout and render the DirectionalBlur witness is already a success.
