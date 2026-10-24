# P01a: OLMBlur: render downsampled previews exactly like the original (no refusal)

## Why (facts)
- In real AE 26.3, preview resolution 1/2 and 1/4 makes OLMBlur refuse with `SmartRender:generic-downsample`, and the user sees black.
- Measured in AE: `ds=1/2`, worlds 960x540; `ds=1/4`, 480x270; in_data 1920x1080.
- The F52 oracle (`~/.cache/olm-emu/worker-F52-geom/`, read `orchestra/reports/F52-oracle-downsample-geometry.md` and `tools/emulation/aexcompat_patches/README-F52.md`) shows the original renders all downsampled Smart cases.
- Seed 1 n100 (`tools/fuzz/measure_F52.py --plugin olmblur`): Smart 19 E / 81 R. Classic 3 E / 79 R / 18 U.
- F52 inference: the original's `0x1800022ee..0x180002315` scales the horizontal amount by a float32 downsample factor, then truncates.

## Do
1. Confirm the original's downsample semantics from disassembly: which params are scaled, x vs y factor, float32 vs double, and the rounding.
2. Implement them generally in the Mac Smart path, and in Classic too if it is cheap, so that downsampled renders follow the same code as full res with scaled params. Remove the `generic-downsample` / `exact-downsample` refusals.
3. **Acceptance:**
   - Rerun `measure_F52.py --plugin olmblur --n 100` with seed 1 and one fresh seed. Smart must be all E except oracle-unavailable cases.
   - Default fuzz: no exact→non-exact, and replay `tests/fuzz_corpus/olmblur*`.
   - Add downsampled witnesses to the corpus. A separate dir or label is fine; keep default replay working.
4. Run the OLMBlur unit tests (`OLM_TEST_JOBS=1`).

## Rules
- Use 1-2 processes. Do not touch the release gate or ledger.
- Change only OLMBlur sources (plus shared core helpers if they are Blur-only).
- The stop rule applies.
