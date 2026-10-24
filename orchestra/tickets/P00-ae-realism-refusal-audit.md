# P00: AE-realism refusal audit: what renders black in real After Effects

## Why (facts, measured by the orchestrator in real AE 2026 26.3 with `OLM_REFUSAL_TRACE` / a scratch host trace)
- In real AE, the user saw OLM Blur, ColorKey and other plugins render **black**.
- Cause: the plugins return the fuzz-era "refusal" error (`PF_Err_BAD_CALLBACK_PARAM`), and AE then shows nothing.
- Observed refusals:
  - `OLMBlur SmartRender:generic-downsample` at preview resolution 1/2 and 1/4. Measured in_data: `ds=1/2` with worlds 960x540 (rowbytes 3840), and `ds=1/4` with 480x270. Full resolution 1920x1080 rendered.
  - `OLMBlur SmartRender:generic-input-world` (×3) in an earlier session. The geometry wasn't captured, probably a layer/ROI case.
  - `OLMColorKey SmartPreRender:prerender-inputs`: `BoundedInDataGeometry` requires downsample 1/1.
- The fuzzer only ever tests "full frame, origin 0, downsample 1:1" at tiny sizes (see `tools/fuzz/adapters/public.py:166`). Real AE use lies largely outside that domain.

## Goal
Measure, without any oracle, which realistic AE situations make each of the 10 shipped bundles refuse or error, and why. This ticket only measures; it makes no plugin changes.

## Do
1. Use the plugin-only host that loads the real `.plugin` bundle:
   - F51 standalone host `~/.cache/olm-emu/worker-F51-x86host/plugin-host`, or F47d (`~/.cache/olm-emu/worker-F47d`). Read their build.json files and the patches in `tools/emulation/aexcompat_patches/`.
   - Build fresh HEAD bundles with `tools/fuzz/build_F47_bundles.py` into `~/.cache/olm-emu/P00/`.
   - Extend the host (as a new patch file, e.g. `P00-host-realism.cpp/.md`) so it can present AE-realistic situations:
     - **downsample** 1/2, 1/3, 1/4, 1/8 and asymmetric (1/2,1/1). Use in_data width/height at full size, world sizes `ceil(full*ds)` as AE does, and in_data->downsample set accordingly;
     - **sizes** 1920x1080, 3840x2160, 1000x1000, odd sizes such as 1279x719, and a layer larger than the comp;
     - **rowbytes padding** (AE-style alignment, plus a deliberately padded case);
     - **extent_hint** smaller than the world, and `PF_Rect` request rects that are a sub-region (region of interest);
     - **output world larger than the input**, where the plugin's PreRender asks for it;
     - **pixel aspect** 0.9 and 2.0;
     - 8/16/32 bpc.
2. For each plugin: run the default params, plus 10 param tuples sampled from `tests/fuzz_corpus/<plugin>/` (those cases are known exact at full res), across that matrix. Record:
   - render OK / refusal tag (`OLM_REFUSAL_TRACE`) / PF error / crash / time;
   - output not-all-zero, as a sanity check.
3. Report a table per plugin of situation → refusal-tag counts, with the refusal source lines.
   - Separate the refusals into three groups: geometry/host-shape refusals (downsample, ROI, padding, size, aspect), exactness-admission refusals (param/size domains never verified), and genuine invalid input.
   - For each tag, note whether the original AEX would plausibly also fail. Cite the disassembly if you checked it.
4. Measure real-size performance too: time per frame at 1920x1080 8/16/32 bpc with defaults. Flag anything over 2 s.

## Deliverables
- `orchestra/reports/P00-ae-realism-refusal-audit.md` with the tables.
- The host patch and a driver `tools/fuzz/ae_realism_audit.py`, committed.
- In `next`: a proposed fix ticket per plugin group.

## Rules
- Use 1-2 processes, and check `memory_pressure` (≥30% free).
- Make no plugin source changes. Do not touch the release gate or ledger.
- Never edit `04_Tools/AEXCompat*`.
- The stop rule applies. Do the defaults at 1920x1080 with ds 1/1, 1/2 and 1/4 for all 10 plugins first.
