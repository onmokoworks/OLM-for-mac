# P01b: OLMDirectionalBlur: downsampled / partial-frame Smart renders without refusal

## Why (facts)
- With the F52 oracle (`~/.cache/olm-emu/worker-F52-geom/`, see `orchestra/reports/F52-oracle-downsample-geometry.md`), the original renders all downsampled Smart cases.
- Mac refuses 80/100 Smart cases (seed 1, `tools/fuzz/measure_F52.py --plugin olmdirectionalblur`):
  - `prerender-partial-frame@2324` ×79. This likely confuses full PF_InData dimensions with the downsampled world dimensions.
  - `smart-generic-world-or-budget@2665` ×1.
- In real AE, users preview at 1/2 or 1/4, so this renders black.
- F52 inference: the original's `0x180003d39..0x180003dac` scales four strength/fade integer fields by downsample and truncates toward zero.

## Do
1. Confirm the downsample semantics from disassembly (fields, factor, rounding).
2. Fix the partial-frame/world guards so that downsampled worlds are handled generally. Remove refusals the original does not share.
3. **Acceptance:**
   - Rerun `measure_F52.py --plugin olmdirectionalblur --n 100` with seed 1 and a fresh seed. Smart must be all E, except where the oracle is unavailable.
   - Default fuzz: no exact→non-exact, and replay the DirectionalBlur corpora.
   - Add downsampled witnesses.
4. Run the unit tests (`OLM_TEST_JOBS=1`).

## Rules
- Use 1-2 processes. Change only DirectionalBlur sources (and the DirectionalBlur-only `core/dblur_*`).
- Do not touch the release gate or ledger. The stop rule applies.
