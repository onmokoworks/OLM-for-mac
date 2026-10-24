# P02h: OLMBlur: render AE-realistic geometry exactly (no Mac-only refusals)

## Witnesses for OLMBlur (F52c seed 1, realistic-v1)
- P01a made downsample exact. Under realistic-v1, Smart still refuses: `SmartRender:generic-input-world@2088` ×55 and `generic-output-world@2089` ×15 (first index 0). These are the input-extent and output-mapping guards for ROI, padding and expanded output.
- In real AE, the user also saw `generic-input-world` refusals at full resolution in one session. Keep the now-exact downsample arithmetic and the Legacy radius-0 behaviour.

## Background (facts)
- In real AE 26.3, a plugin that refuses returns `PF_Err_BAD_CALLBACK_PARAM`, and the user sees **black**.
- AE routinely uses downsampled previews (1/2, 1/4). It also requests sub-rectangles (ROI) when a comp is zoomed or partly visible, and allocates outputs from PreRender's `result_rect`.
- F52c (`orchestra/reports/F52c-geometry-hosts-and-campaigns.md`, `F52c-evidence/summary.json`) built a geometry-negotiating oracle, `~/.cache/olm-emu/` INDEX entry F52c. It also built qualified source and bundle hosts, and the `--geometry realistic` sampler (realistic-v1).
- Under that sampler, **the original rendered successfully in every refused witness**. The Mac refusals listed below are therefore Mac-only, and each one shows up as black in AE.
- P01a/b/c already fixed downsample for Blur, DirectionalBlur and ColorKey. Their reports show the pattern: confirm the original's arithmetic from disassembly, generalize the geometry handling, and remove the refusal.

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
