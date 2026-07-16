# OLMDistanceGradation RenderBits Host/Resize Staging Audit

Date: 2026-07-17

## Decision

The PF8 helper, field, and compose boundaries remain closed. The active Mac-only
boundary is the host-world/resize staging around `RenderBits`. This audit adds a
bounded executable differential for layout and typed staging only. It does not
claim AE exactness, Windows AEX equivalence, or a recovered non-identity resize
kernel.

## Contracts recovered

| Contract | Evidence | Result |
| --- | --- | --- |
| Mac `RenderBits` dimensions | `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:850-852` takes `w/h` from `output->width/height`; input reads are bounded by those loop dimensions. | Same-shape staging is required before the production body. |
| Mac row access | `...cpp:858-859` and `873-877` address each row with the world `rowbytes`. | Arbitrary padded rowbytes are preserved; active bytes are `width * sizeof(P)`. |
| Mac depth dispatch | `...cpp:894-900` selects `PF_Pixel8`, `PF_Pixel16`, or `PF_PixelFloat`. | No cross-depth conversion is introduced by the Mac `RenderBits` body. |
| AEX world descriptor | `decomp/DistanceGradation.aex.c.txt` compose callbacks use world offsets `data + 0x18`, `rowbytes + 0x20`, `width + 0x24`, `height + 0x28`. | The bounded model uses the same descriptor fields. |
| AEX active-row copy | `FUN_181171d00` / siblings copy `width * 4`, `width * 8`, or `width * 0x10` bytes per row, stepping destination by its rowbytes. | Padding is outside the copy region and must remain untouched. |
| AEX typed field staging | `FUN_181170870`, `FUN_181170480`, and `FUN_181170c90` read 4/8/16-byte pixels; `FUN_181174760` selects depth constants for the float working stage. | Scale constants are recorded as 255, 32768, and 1 for 8/16/float. |
| Resize | The dump contains same-shape OpenCV resize activity in field preparation, but does not bind a host-world non-identity resize allocation/copy contract. | Non-identity resize is rejected by the audit and remains unresolved. |

## Executable differential

Run:

```text
python3 tools/emulation/test_olmdistancegradation_renderbits_host_resize_staging_20260717.py
```

It checks 8/16/float active-row copies, tight internal rowbytes, padded output
canaries, typed depth scales, rejection of a non-identity resize, and the six
existing bounded production `RenderBits` fixtures. The comparison is a Mac
layout/staging contract check, not an AEX or AE render comparison.

## Next allowed action

Keep production, EDT, compose, store, and ledger untouched. A stronger claim
requires a captured Mac host-world allocation/resize trace or an equivalent
Windows-bound witness that identifies source/output dimensions, rowbytes,
allocation depth, copy regions, and conversion order for a non-identity case.
