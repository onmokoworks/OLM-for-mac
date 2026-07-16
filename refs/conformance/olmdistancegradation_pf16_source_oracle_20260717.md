# OLMDistanceGradation PF16 Mac Source Oracle

Date: 2026-07-17 (Mac)

This evidence compares the current 8x5 actual-AEX PF16 Iterate16 fixture with
an independently compiled Mac source oracle. The oracle source-includes the
current production `mac/OLMDistanceGradation/OLMDistanceGradation.cpp` and
calls `RenderBits<PF_Pixel16>`, which runs production field generation and
`shade_scanline<PF_Pixel16>`/`compose_pixel`. It does not copy expected words.

## Exact run

```text
python3 -m py_compile tools/emulation/probe_dg_pf16_wrapper_entry_20260717.py tools/emulation/test_dg_pf16_source_oracle_20260717.py
python3 tools/emulation/test_dg_pf16_source_oracle_20260717.py > /tmp/dg-oracle-20260717.json
```

The process exited `0`. The result was `blocked` because the byte comparison
failed closed after both executions completed successfully and the
parameter/world contract assertions passed.

## Control and discriminating branch

- Current control: `refcon+0x90=1` (degenerate/use-background), actual AEX
  status `PASS`, 40 compose entries, but equality is explicitly
  `non-discriminating` because the branch bypasses field reads.
- Smallest branch fixture: only `refcon+0x90` changed from `1` to `0`.
  Parameters, 8x5 geometry, source words, rowbytes, and padding canaries were
  unchanged.
- Non-degenerate actual AEX: `PASS`, 40 compose entries, padding preserved.
- Mac source oracle: return code `0`; it called production
  `RenderBits<PF_Pixel16>` and preserved its output padding canary.
- Contract assertion: `PASS`. Gradient/background float bytes, scalar modes,
  and source-world active bytes match. Production's raw `INTERP_LINEAR=2` and
  the AEX refcon's raw `interp_mode=1` are recorded as the same semantic
  `Linear` mode.

## Comparison

Active output is 320 bytes (`40 * 8`). It is not byte-equal:

```text
active_byte_equal=False
byte_mismatch_count=160
first_mismatch_byte=2
actual-AEX unique A,G,R,B words: [(32768, 0, 0, 0)]
Mac source unique A,G,R,B words: [(32768, 3598, 0, 30583)]
```

The actual-AEX active SHA-256 is
`f7d3ab8608430f32b72351c8c681a36de5845e61bf1c83d34340abbbb9ad4d5f`.
The source-oracle active SHA-256 is
`671dbfeaeeaf7c953f652cc08052f56e16daf1d69203c0ffaa6d756d05c68b8e`.

Both runs preserved the 12-byte-per-row `0xA5` padding canary. The source
oracle padding SHA-256 is
`aabad596d9727bb3c8e76e49409af32b4457774332b964cbfde683b75e533360`.

## First-divergence capture

The actual wrapper-produced field world was read immediately before the
Iterate16 compose call for all 40 active pixels. Its active field SHA-256 is
`7b6436b0c98f62380866d9432c2af0ee08ce16a171bda6951aecd95ee1307d61`; every
pixel was raw A,G,R,B `[0, 0, 0, 0]`, and every field X value was `0.0`.

The Mac production `build_distance_field` bridge consumed the same 8x5 source
world and exposed the exact input to production `shade_scanline`. Its active
field SHA-256 is
`54ce1783a09fc0934862ee25f7c499122d59fdb961ee3079228938a44d1394e2`; every
pixel was raw A,G,R,B `[0, 32768, 0, 0]`, and every field X value was `1.0`.
The production field return code was `0`, and all 40 normalized source alpha
values were `1.0`.

The first differing active output byte was byte `2` (160 differing bytes of
320). The field raw words and X values were both unequal, so the bounded
classification is `fieldgen_or_staging`, before compose layout. A first
compose call on the AEX side observed `degenerate=0, inout=3, use_bg=1,
invert=1, render=1, interp=1, power=1.0`, gradient RGB float values
`[0.10980392247438431, 0.0, 0.9333333373069763]`, black background, and source
pixel A,G,R,B `[32768, 0, 0, 0]`. The source contract has the same semantic
values and source pixel; only the raw production enum is `INTERP_LINEAR=2`
versus AEX refcon `1`, both recorded as semantic Linear. Compose contract
match is `true`.

This remains fail-closed Mac-local evidence. It makes no Windows or AE-exact
claim and does not claim production/ledger edits.

## Provenance

- Production source SHA-256:
  `8fa772b65419281b81a1a4eb37618771d210c4728b54aa73cb29f9f610e9e6d8`
- Oracle bridge:
  `tools/emulation/dg_pf16_source_oracle_20260717.cpp`
- Oracle bridge SHA-256:
  `1e40ceb459b69d3dc8405243a1de20059e665a8c65fdf066efea004f32536b88`
- AEX SHA-256:
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`

The earlier black-vs-purple result was invalid as a production comparison
because the AEX refcon gradient fields were zero. This is the first comparison
after the contracts are aligned; it remains bounded Mac-local evidence and
makes no Windows or AE-exact claim.
