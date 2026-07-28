# OLMDistanceGradation PF16 field-pack producer: static 2025 AEX audit

Date: 2026-07-28

## Verdict

The 2025 Windows binary statically identifies the producer and transfer chain
for the PF16 field word consumed at `DistanceGradation+0x117057d`.

The direct word is **not** produced at the compose callback and it is **not**
the logging-only `nearest_even(float32 * 32768)` value in the Mac capture
schema.  In the 16bpc render family, an already PF16-code-domain, four-channel
OpenCV matrix is converted to the destination matrix by `cvConvertScale` with
`alpha=1.0`, `beta=0.0`; each converted row is then copied byte-for-byte into
the AE field world.  Compose subsequently reads the red/first color word at
`[RCX+2]`.

The static evidence does not contain a case-bound direct memory value and does
not, by itself, prove the process MXCSR rounding mode.  Therefore it identifies
the binary producer and conversion boundary, but cannot replace the r3 direct
typed capture with a derived nearest-even word.

## Exact 16bpc producer chain

All addresses below are RVAs in the hash-pinned 2025 AEX:
`a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`.

1. `+0x1171c0b` calls `FUN_18117c6e0` after field generation/optional blur.
   Its result is the four-channel source matrix held in `RDI`.
2. At `+0x1171c10`, `XMM3` is zeroed (`XORPS XMM3,XMM3`).
3. At `+0x1171c13`, `XMM2` loads the double at `+0x1504aa0`. Direct PE-byte
   decoding gives `1.0`.
4. At `+0x1171c1b`, `RDX` loads the destination matrix wrapper from
   `[RBP-0x78]`; at `+0x1171c1f`, `RCX=RDI` selects the source matrix.
5. `+0x1171c22` calls `FUN_18117c580(RCX=source, RDX=destination,
   XMM2=1.0, XMM3=0.0)`.
6. `FUN_18117c580` is the binary's `cvConvertScale` wrapper (the embedded
   diagnostic names `modules/core/src/convert_c.cpp`). It preserves the
   arguments in `XMM6/XMM7` at `+0x117c5a9/+0x117c5a6`, constructs the OpenCV
   array wrappers, and calls the OpenCV conversion dispatcher
   `FUN_1811a3020` at `+0x117c655`, with scale in `XMM3` and beta on the stack.
   `FUN_1811a3020` identifies itself through the embedded
   `cv::Mat::convertTo` diagnostic from `convert.dispatch.cpp`.
7. The 16bpc caller computes `width * 8` at
   `+0x1171c2b..+0x1171c2f`. For every row, it obtains source data from the
   converted matrix at `+0x1171c53..+0x1171c57`, obtains the AE field-world
   row from `[RSI+0x18]` at `+0x1171c5b..+0x1171c5e`, and calls the binary's
   `memcpy` thunk `FUN_1813a03c6` at `+0x1171c65` with
   `RCX=field_world_row`, `RDX=converted_mat_row`, `R8=width*8`.
8. In `FUN_181170480`, the compose callback derives the field pixel address at
   `+0x1170562..+0x1170571`, then `+0x117057d` executes
   `MOVZX EAX,word ptr [RCX+2]`. `+0x117058a..+0x11705a7` converts that direct
   word to float and multiplies it by the float constant `1/32768`.

The neighboring render families corroborate the depth selection: their final
row-copy widths are `width*4` at `+0x117293b..+0x117293f` and `width*16` at
`+0x117364b..+0x117364f`; the `width*8` family above is uniquely PF16.

## Scale and rounding: what is and is not proved

The upstream depth scale is separate from the final conversion. At
`+0x11719f7..+0x1171a04`, depth `0x10` selects the double at
`+0x1504ab8`; direct PE decoding gives `32768.0`. That value is supplied to
the preceding normalization wrapper. By the time `+0x1171c22` runs, the
matrix is already in PF16 code units, so the final `cvConvertScale` uses
`alpha=1.0`, not another multiplication by 32768.

Existing OpenCV 4.5.5 and actual-AEX focused fixtures establish that the
conversion under the tested default environment rounds ties to nearest even
(`1.5,2.5,3.5 -> 2,2,4`, among the recorded witnesses). This is a valid
derived model of the conversion. Static disassembly, however, selects a
conversion function through a dispatcher and does not establish the live
MXCSR value for an AE process. The direct field staging word remains the
16-bit memory result copied at `+0x1171c65`; it must be captured as memory to
be a case-bound direct witness.

## Consequence for the 2026-07-28 schema/r3 package

`tools/emulation/olmdistancegradation_pf16_boundary_capture_schema_20260728.json`
correctly keeps these concepts separate:

- `derived_pf16_word` is logging-only nearest-even derivation from the Mac
  float boundary;
- `direct_field_staging_word` is unavailable on that Mac boundary;
- the r3 Windows hook at `+0x117057d` is the required direct typed read.

Static evidence can improve a future producer hook: stop on the 16bpc
`memcpy` call at `+0x1171c65`, gate the destination interval against the
field-world address later observed in `RCX` at `+0x117057d`, and read the
corresponding source word from `RDX` before the copy. It cannot manufacture
the missing direct word from the schema's float value.
