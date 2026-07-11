# AEX CPU Fixture Template Result - 2026-07-10

## Verdict

The first reusable AEX CPU fixture loop is operational for
`OLMDistanceGradation`. This is function-level binary evidence, not `AE exact`.

## Contract

- Schema/verifier: `tools/emulation/fixture_contract/`
- Provenance distinguishes `windows-aex-cdb`, `unicorn-aex`, and
  `portable-core`.
- Parameter origin distinguishes runtime-captured, binary-built, and
  harness-constructed blocks.
- Buffer descriptors require exact ranges, SHA-256, dimensions, rowbytes,
  bit depth, and explicit channel order. Scalar float fields and the observed
  DistanceGradation `A,G,R,B` 16-bit order are represented without pretending
  they are ordinary ARGB.

## DistanceGradation facts

### Synthetic fieldgen fixture

- Real AEX function: `FUN_181174760` at `0x181174760`
- Binary SHA-256:
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- Input: `17x11` uint8 mask, threshold `3`, `param8=1`
- AEX output: `748` float32 bytes
- Portable C++ output: byte exact (`mismatched_bytes=0`)
- Committed fixture:
  `tools/emulation/fixtures/distancegradation_fieldgen_synthetic_17x11/`

The fixture first rejected a TRUNC interpretation with `184` mismatched bytes.
The actual `param8=1` branch is binary thresholding; correcting that branch
made the portable output exact.

### Real case_0023 fieldgen

The full `1920x1080` case input was executed through the same real AEX helper.

| Pass | Threshold | Mask | AEX/portable bytes | Output SHA-256 |
| --- | ---: | --- | ---: | --- |
| inside | `36` | source alpha | `8,294,400`, exact | `0ade5024e5c351e27f44dc5987b4d162735ab38af308c6c2256b34fad96624f7` |
| outside | `0` | inverted source alpha | `8,294,400`, exact | `7186110f48f4fe1b3d212c478b56673387c76ef31bcebca732bb17ba41bb9e06` |

This second pass rejected an incorrect threshold floor-to-one rule with
`20,420` mismatched float values. Preserving threshold zero made both passes
exact.

### Compose fixture

- Real AEX function: `FUN_181170480` at `0x181170480`
- Case points: `(414,393)`, `(415,393)`, `(416,393)`
- Actual AEX fieldgen values: `0,1,1`
- Packed field words consumed by compose: `0,32768,32768`
- Actual AEX compose output: `24` bytes in `A,G,R,B` word order
- Portable C++ compose output: byte exact (`mismatched_bytes=0`)
- Committed fixture:
  `tools/emulation/fixtures/distancegradation_compose_case0023_triplet/`

The compose fixture now stores a relocatable `binary-built` parameter block:
the emulator world pointers at `+0x00/+0x08` are zeroed, relocation targets are
declared in the manifest, and the callback's scalar range `+0x90:+0xd4` is
preserved. Its basis is the AEX callback layout plus the case manifest; it is
not described as a Windows runtime-captured block.

## Mac integration

The Mac `OLMDistanceGradation` target now builds
`core/olmdistancegradation_fieldgen.cpp` directly and delegates its
distance-transform/threshold/normalize stage to that shared implementation.
The adapter still owns bit-depth mask extraction, feature dispatch, blur,
compose, and writeback.

Independent checks after integration:

- synthetic AEX field fixture: `748` bytes exact
- case_0023 inside field: `8,294,400` bytes exact
- case_0023 outside field: `8,294,400` bytes exact
- AEX compose triplet: `24` bytes exact
- brute-force distance-stage oracle: `280` values passed
- Xcode Debug target: Universal `arm64 + x86_64` build succeeded

This strengthens the `binary-grounded` implementation path. It does not change
the correctness status to `AE exact` without a Mac AE render comparison.

## RadialBlur side lane

`tools/emulation/probe_radialblur_final_plane_small.py` now reaches the real
AEX post-normalization boundary `0x180005d99` on a `32x32` direct geometry. It
grounds:

- angle count `4`, radial count `49`,
- final, accum, denominator, and validity plane pointers,
- one actual-AEX prepass call and one actual-AEX scatter call,
- four typed final-plane cells.

The earlier `4x1` run was zero because the direct harness omitted the real AEX
`FUN_180008690` parameter setup. With that setup restored, all `196/196`
accum/denom/valid cells are informative. The probe maps bounded output controls
`(7,0)`, `(8,0)`, and `(24,0)` through the actual AEX inverse transform to
their four-cell sampler neighborhoods. This is a nonzero small-plane witness,
but the bounded crop is not the full-frame case_0009 semantic oracle and does
not authorize a Mac source change by itself.

## Verification

```sh
python3 refs/scripts/smoke_dg_cpu_fixture.py
python3 refs/scripts/smoke_dg_case0023_cpu_fixture.py
python3 refs/scripts/smoke_radialblur_final_plane_small.py
```

All three commands pass. DistanceGradation's compose fixture provenance is now
`binary-built`; a same-run Windows capture remains a stronger optional oracle,
not a prerequisite for portable replay. The next RadialBlur task is one
re-scoped Windows confirmation of the concrete
typed sampler cells selected by the bounded nonzero witness.
