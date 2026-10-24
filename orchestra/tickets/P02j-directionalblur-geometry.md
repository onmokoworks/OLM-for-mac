depends: T15-odd-even-random-comp-sweep
# P02j: OLMDirectionalBlur: render AE-realistic geometry exactly (ROI / negotiated output rect)

## Witnesses (T15 prerequisite run, F52c, realistic-v1 seed 2026 n20: Smart 12 E / 8 M / 0 R)
- Read `orchestra/reports/T15-odd-even-random-comp-sweep.md`, `T15-evidence/local-fix-experiments.json`. Saved witness: `tests/fuzz_corpus/olmdirectionalblur/T15-prerequisite-realistic/rectangle.json` (replay with `--geometry realistic`).
- All 8 mismatches are **output-rect mismatches**: PF8 sampled 42x1, original result [16,0,34,1], Mac [0,0,42,1]. Reduced: 5x1, original [1,0,5,1], Mac [0,0,5,1].
- `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:2337` replaces the request with the full sampled bounds, and `:2362` advertises the full rect as result.
- **Already refuted** (do not retry as-is): (1) forwarding the incoming request only, and (2) advertising the requested rect while keeping full input checkout. Both turn the mismatch into refusal 516 at `RenderWorld:deep-copy-world@1482`. A real fix must handle the render-world ownership/copy contract (output world smaller than / offset from the input) as well as PreRender bounds, as P02h did for Blur and P02d for RadialBlur.

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
