# OLMDistanceGradation 8bpc First-Stage Residual-Family Probe

Date: 2026-07-16

## Scope

Mac-only local evidence. The probe is
`tools/emulation/probe_dg_8bpc_first_stage_residual_family_20260716.py`.
It loads the actual current AEX under the repository's Unicorn emulator and
uses a one-pixel fixture. It does not edit production code, claim Windows
internal values, or claim AE exactness.

## FACT

- The loaded AEX SHA-256 is
  `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.
- The shared 8bpc callback is `0x181170870`. The decompilation and the live
  call agree on Windows x64 ABI: `RCX=refcon`, `RDX=x`, `R8=y`, and the fifth
  argument at `[RSP+0xe0]` is the output pointer.
- The actual AEX reaches the field read block at `0x18117098f`, the source
  read block at `0x181170a09`, the pre-u8 block at `0x181170c20`, and the
  post-store boundary at `0x181170c40` for the one-pixel fixture.
- The four output byte stores are at `0x181170c29` -> `out+1`,
  `0x181170c30` -> `out+3`, `0x181170c37` -> `out+2`, and `0x181170c3e`
  -> `out+0`. This is memory order `A,G,R,B`, matching the decompilation.
- The probe's three fixtures are discriminating: changing only field green
  from `100` to `101` changes output memory from `[255,37,221,24]` to
  `[255,36,220,24]` while source bytes remain fixed; changing source bytes to
  `[110,120,130,200]` while field green remains `100` and `Gradation=2`
  changes the source-read witness and output result to `[255,75,159,133]`.
  The pre-u8 values and all
  four stores are captured before the callback returns.
- The existing residual facts remain: case `0001` is `57,0,0,57` versus
  `56,0,0,56`; case `0015` is `0,0,0,10` versus `10,0,0,10`; case `0029` is
  `7,0,60,64` versus `7,0,63,67`, in PNG-facing RGBA order.

## INFERENCE

- The first stage common to all three residual signatures that is both
  addressable and discriminable locally is the **U8 pre-store/writeback
  boundary**, beginning at `0x181170c20` and ending after the four stores at
  `0x181170c40`. It is the only shared stage that directly owns the observed
  byte-order positions and truncating `CVTTSS2SI` conversion.
- This narrows the investigation to the values entering the U8 boundary and
  its byte conversion/store order. It does **not** prove that the Mac/Windows
  difference is caused by writeback; a prior field/source/compose value could
  still differ and arrive at the same boundary.
- The smallest truthful live witness is therefore one fresh 8bpc process per
  case, with the callback ABI above and these exact stops: entry
  `0x181170870`, field `0x18117098f`, source `0x181170a09`, pre-u8
  `0x181170c20`, each store `0x181170c29/0x181170c30/0x181170c37/0x181170c3e`,
  and post-store `0x181170c40`. The witness must retain field/source addresses,
  pre-u8 values, output address, and post-store bytes.

## Result

The live Windows binding is unavailable in this Mac-only task. The exact stop
addresses, ABI, and one-pixel discriminating fixture are proven locally. No
production tuning or residual-family closure is justified from this probe.
