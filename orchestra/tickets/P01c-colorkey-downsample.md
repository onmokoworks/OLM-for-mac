# P01c: OLMColorKey: downsampled Smart renders (prerender refusal + 7 mismatches)

## Why (facts)
- In real AE, ColorKey's `SmartPreRender` refuses (`prerender-inputs`) because `BoundedInDataGeometry` requires downsample 1/1. Previews at 1/2 or 1/4 therefore render black.
- With the F52 oracle and the downsample forwarded (`tools/fuzz/measure_F52.py --plugin olmcolorkey`, seed 1 n100), Smart is 93 E / 7 M.
  - Mismatch indices: 3, 12, 27, 31, 33, 87, 93, all downsampled.
  - First: index 3, full 39×45 → 10×12, PF16 at 1/4. 27 differing words; word 0 is original `c634` vs Mac `d634`.
- F52 found inverse-coordinate-scale helpers in the original, but did not confirm their callers or the radius rule (edge thin/blur amounts?).

## Do
1. Find from disassembly how the original applies downsample: edge thin/blur radii, scaling, rounding.
2. Implement that generally. Remove the downsample refusal in the real-AE path, and check that the measure harness exercises the same path.
3. **Acceptance:**
   - Rerun `measure_F52.py --plugin olmcolorkey --n 100` with seed 1 and a fresh seed. Smart must be all E.
   - Default fuzz: no exact→non-exact, and replay the ColorKey corpora.
   - Add downsampled witnesses.
4. Run the unit tests.

## Rules
- Use 1-2 processes. Change only ColorKey sources.
- Do not touch the release gate or ledger. The stop rule applies.
