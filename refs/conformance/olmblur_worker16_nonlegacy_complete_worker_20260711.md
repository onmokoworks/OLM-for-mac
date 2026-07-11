# OLMBlur 16bpc Non-Legacy Complete Worker - 2026-07-11

## Scope

This lane targets the actual 16bpc Non-Legacy worker `FUN_180002280` and uses
the exact `FUN_180001000` / `FUN_180001980` helper core. It stages PF_Pixel16
as little-endian A/R/G/B, performs six horizontal or vertical subpasses per
repeat, applies the captured decay/weights, and uses the AEX `+0.5`, truncating,
clamped 16-bit writer.

The portable build disables contraction with `#pragma STDC FP_CONTRACT OFF`,
`-ffp-contract=off`, and `-fno-fast-math`.

## Actual-AEX Fixtures

`tools/emulation/test_olmblur_worker16_nonlegacy.py --export` calls
`FUN_180002280` with the actual four-argument worker ABI:
`context, source_world, output_world, params`. The worlds use the grounded
`+0x18/+0x20/+0x24/+0x28/+0x2c` data, rowbytes, width, height, and depth
fields; the parameter block sets depth `16`, Legacy `0`, amount, smoothness,
repeat, and bias direction.

The regenerated fixture manifest records the AEX SHA-256 and complete output
buffers for both the basic and large-radius/reverse-direction cases. Expected
buffers are captured from the AEX, never encoded from the portable output.

## Verification

The replay compares every byte of each complete A/R/G/B output buffer. On a
portable mismatch it emits `BOUNDARY` with the first byte, pixel, coordinate,
channel, actual byte, and AEX byte. This is a real `0x2280` boundary report,
not a `FUN_180005f20` host-layout classification.

No Mac, ledger, or NAS files were changed.
