# OLMDistanceGradation 0010/0011 Compose Exact-Address Local Witness

Date: 2026-07-10

## Classification

`local_actual_aex_bounded_witness`; this is not a Windows live exact-address
return and does not promote the DG family to exact.

## FACT

- The real `plugins_2025/DistanceGradation.aex` was executed under Unicorn at
  `FUN_181170480` (`0x181170480`), with two calls and a `200000` instruction
  cap per call.
- The disassembly-backed world formula is
  `base + y * rowbytes + x * pixel_size`; the callback reads the field scalar
  from `RCX + 0x2` and the source/shade pixel from `RDX + 0x2`.
- The accepted Windows source/output geometry is `rowbytes=0x3c00`,
  `pixel_size=8`, so the full-frame output formula is
  `output_base + y * 0x3c00 + x * 8`.
- The local harness used `1920x1080`, `rowbytes=15360`, and `8-byte` pixels.
  Local bases are synthetic Unicorn heap addresses and must not be read as
  Windows pointer evidence.

| XY | Local field address | Local source address | Local output address | Field words | AEX output words | Windows A word |
| --- | --- | --- | --- | --- | --- | ---: |
| `(6,40)` | `0x21068030` | `0x20096030` | `0x21fa4000` | `0000 733c 0000 0000` | `0cc4 0000 8000 0000` | `3268` |
| `(901,394)` | `0x21599428` | `0x205c7428` | `0x21fa4008` | `0000 598c 0000 0000` | `2694 0000 8000 0000` | `9876` |

The local AEX alpha words are `3268` and `9876`, matching the accepted
Windows PF16 store words. The local field scalars are respectively
`29500/32768 = 0.9002685546875` and `22892/32768 = 0.6986083984375`; the
corresponding modeled `1-X` values are `0.0997314453125` and
`0.3013916015625`.

## INFERENCE

- A bounded actual-AEX compose witness is feasible and shows that the two
  Windows-required field words, when supplied to the real compose callback,
  produce the two Windows alpha store words. This supports the compose/store
  address and arithmetic shape, but it does not prove that Windows packed or
  consumed those words at the upstream field producer.
- The local callback's interleaved word order is represented as `A,G,R,B` in
  the existing harness convention; the field read is the second word at
  `+0x2`. Semantic channel naming at this offset remains less important than
  the binary offset and is not used to infer a Mac change.
- No global field-pack or final-rounding rule follows: the two witnesses still
  require opposite floor/ceil relationships from the current float field.

## Exact Blockers

1. The Windows exact-address return did not provide a field-world base,
   field rowbytes/layout, `RCX` words, compose scalars, or same-run final
   writer values for `(6,40)` and `(901,394)`.
2. The Windows source/output bases are known, but the field address formula
   cannot be instantiated with a Windows field base until a live field-world
   header or exact `RCX` address is returned.
3. The local witness uses harness-constructed field words, so it cannot decide
   whether the floor/ceil split occurs during Windows field packing, world
   readback, or an earlier host conversion.

## Smoke

Command:

```text
python3 tools/emulation/olmdg_compose_exact_address_witness_20260710.py
```

Result: PASS. The real AEX callback completed in `272` total instructions for
the two calls; both local AEX alpha words matched the accepted Windows store-A
words. JSON details are in
`refs/conformance/olmdg_compose_exact_address_witness_20260710.json`.

No Mac source, ledger, existing artifact, or NAS path was edited.
