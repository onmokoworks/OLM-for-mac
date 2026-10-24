depends: T15-odd-even-random-comp-sweep
# P02i: OLMColorKey: render AE-realistic geometry exactly (ROI, negotiated output; no Mac-only refusals)

## Witnesses (T15 prerequisite run, F52c, realistic-v1 seed 2026 n20: Smart 10 E / 6 M / 4 R)
- Read `orchestra/reports/T15-odd-even-random-comp-sweep.md` and `T15-evidence/`. Saved witnesses: `tests/fuzz_corpus/olmcolorkey/T15-prerequisite-realistic/{refusal,pixels}.json` (replay with `--geometry realistic`).
- **Refusal** `PrepareRenderWorld:public-admission@2598`: PF16, full 94x1, sampled 24x1, ds 1/4, extent [0,0,10,1]. Reduced: sampled 3x1, the original succeeds and Mac returns 516. The relevant restriction is `mac/OLMColorKey/OLMColorKey.cpp:2520-2523` (complete extents / equal dimensions for non-pixel-local processing).
- **Pixel mismatch** with the same output rect: PF8 sampled 42x1, output [16,0,34,1]. Reduced: 5x1, output [1,0,5,1], byte 0 original `ff`, Mac `00`. Pointers: `RenderTyped` `:1832-1834` (origin offset in source reads, working arrays sized from output). Confirm the original's ROI source addressing and neighbourhood staging from disassembly / intermediate values before changing code.
- T15 also fixed a host defect (ColorKey PreRender bitdepth was 0); it is merged.

## Background (facts)
- In real AE 26.3, a plugin that refuses returns `PF_Err_BAD_CALLBACK_PARAM`, and the user sees **black**.
- AE routinely uses downsampled previews (1/2, 1/4). It also requests sub-rectangles (ROI) when a comp is zoomed or partly visible, and allocates outputs from PreRender's `result_rect`.
- F52c (`orchestra/reports/F52c-geometry-hosts-and-campaigns.md`, `F52c-evidence/summary.json`) built a geometry-negotiating oracle, `~/.cache/olm-emu/` INDEX entry F52c. It also built qualified source and bundle hosts, and the `--geometry realistic` sampler (realistic-v1).
- Under that sampler, **the original rendered successfully in every refused witness**. The Mac refusals listed below are therefore Mac-only, and each one shows up as black in AE.
- P01a/b/c already fixed downsample (1:1-origin, full-frame) for Blur, DirectionalBlur and ColorKey; ROI / negotiated output was not covered there. P02a-h fixed the other eight plugins under realistic-v1; read those reports and diffs as the pattern (e.g. P02h Blur full-layer checkout + RETURNS_EXTRA_PIXELS, P02d RadialBlur request/result rects).

## Scope
- **The Smart route is the contract** (T14 decision in `notes/KNOWN_ORIGINAL_BUGS.md`). The exception is Smoother v1, which is Classic-only, so its Classic route is the contract.
- Leave the Classic route alone except for Smoother v1.
- Real-AE geometry comes first: downsample, sub-rect requests, `result_rect`-sized and expanded outputs, and padded rowbytes. Handle `extent_hint` and pixel aspect the way the original does. If the original ignores them, ignore them too.

## Acceptance
- Seed 1 plus one fresh seed, n100, `--geometry realistic` (see `tools/fuzz/measure_F52c.py`): the contract route must have **0 Mac-only refusals and 0 mismatches**, excluding cases where the oracle is unavailable.
- Default geometry: no exact→non-exact on the default fuzz (seed 1, n300), and replay all of this plugin's corpora.
- Add realistic witnesses as a separate labelled corpus set.
- Run the plugin's unit tests (`OLM_TEST_JOBS=1`) and compare before vs after. Pre-existing historical failures may stay; just list them.

## Rules
- Use 1-2 processes. Change only this plugin's sources and its plugin-only core helpers.
- Do not touch the release gate or ledger, and never edit `04_Tools/AEXCompat*`. Do not rebuild the oracle.
- The stop rule applies. Partial progress, such as "downsample + ROI fixed, aspect pending", is valuable.
