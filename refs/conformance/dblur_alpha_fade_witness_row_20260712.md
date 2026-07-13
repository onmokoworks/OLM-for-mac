# DirectionalBlur Alpha Fade bounded witness row

Status: `pass`; production unchanged.

## Scope

This harness covers the surviving Mac-vs-current-Windows witness at host
`(1308,184)`, with Front Strength `240`, Front Alpha Fade `96`, angle `0`, and
the captured PREMULTIPLIED-input PF world. It does not invoke the `2206x2206`
full render entry. It invokes actual-AEX `FUN_1800038d0` for one `2206`-pixel
row, which includes the complete prepass and scatter ownership footprint.

## FACT

- Existing full-render evidence gives work dimensions `2206x2206` and host
  padding `(143,563)`. Angle `0` becomes rotate-in `+pi/2` and rotate-back
  `-pi/2`.
- Host `(1308,184)` is work destination `(1451,747)`. Exact float32 rotate-back
  arithmetic samples internal `(747,755)` with `fx=fy=+0.0`.
- The full residual extent `(1308,184..517)` maps to one internal row:
  `(747..1080,755)`. Rotate-in at that row samples captured host column `1308`
  exactly, so the harness materializes only that row from the raw PF world.
- The actual AEX receives the validated UCRT `n=96` and `n=240` table words.
  A pointer-biased one-row invocation preserves the real row arguments
  `755..756` and full height `2206`; `FUN_1800038d0` executes `4,196,879`
  instructions without allocating or processing the full plane.
- Actual-AEX and portable destination, denominator, and alpha buffers are
  byte-identical over the complete row and the focused witness extent. Their
  differing-float counts are all zero.
- Direct execution of the AEX normalization loop at `0x180005554` through the
  boundary before `0x180005610` executes `44,412` instructions. Its normalized
  destination is byte-identical to the portable float32 divide; SHA-256 is
  `2605a4dfc67b6a5a3386754602c3fb34e44f6ba607b5f7d6cc52a413fa2821c0`.
- At this angle the rotate-back coordinates have `fx=fy=+0.0`. The helper's
  top-left weight is one, all other weights are zero, and its ordered adds
  preserve the focused source values exactly.
- Direct actual-AEX `FUN_180006b30` calls pack all `334` focused pixels using
  the normalized row. Those bytes equal the portable truncating writer, but
  differ from the captured Windows PF output at exactly `226` pixels. The AEX
  direct-pack SHA-256 is
  `9b90145bf4323ea96a902de2e77b57db5367d62d803e0a91b070c5a3250bc794`;
  the Windows-column SHA-256 is
  `e69f3865bd321c56823a503d67f3410e2cda0674e0b32860f914dca38a3e7570`.

## INFERENCE

Normalization operation order, rotate-back copy behavior, and PF quantization
are not the first mismatch. Given the bounded row state, the actual AEX agrees
with the portable core through all three boundaries and produces the known Mac
bytes rather than the captured Windows bytes.

The remaining missing FACT is an in-situ capture of destination, denominator,
and alpha for full-render row `755`, after the real worker schedule returns and
immediately before normalization at `0x180005554`. The isolated actual-AEX
rowdriver result cannot establish that the full render enters normalization
with the same state. No assembly-grounded production difference is proven, so
production remains unchanged.

## Commands

```sh
python3 tools/emulation/test_dblur_alpha_fade_witness_row_20260712.py
python3 refs/scripts/smoke_dblur_alpha_fade_witness_row_20260712.py
```

Both commands run the bounded row only. Neither runs the full entry or writes
PNG output.
