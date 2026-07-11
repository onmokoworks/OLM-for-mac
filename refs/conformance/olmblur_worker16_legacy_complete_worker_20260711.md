# OLMBlur 16bpc Legacy Complete Worker

Date: 2026-07-11

## Scope

This artifact is the portable `FUN_180005f20` worker slice. It uses the exact
Legacy `FUN_1800014f0` / `FUN_180001ea0` helper core and does not modify Mac
code, the ledger, or NAS-related files.

## Grounded behavior

- Stages little-endian PF16 A,R,G,B words into RGB float planes and a one-byte
  validity plane. Any nonzero alpha word is active.
- Uses the render-scaled Legacy radius, smoothness-derived sigma, and centered
  symmetric weights for each repeat.
- Performs six contiguous horizontal or vertical subpasses per direction,
  swapping the two RGB planes in the AEX order for Bias Direction `1` or `2`.
- Uses the Legacy 16bpc word writer: `floor(value + 0.5)`, clamped to
  `0..32768`, while preserving the copied alpha word.

## Fixture gate

The actual AEX is pinned to SHA-256
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` and the
worker entry is `0x180005f20`. Fixtures live under
`tools/emulation/fixtures/olmblur_worker16_legacy/`.

| Case | Size | Radius | Repeat | Bias | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `16bpc_legacy_basic` | 12x12 | 3 | 2 | 1 | exact |
| `16bpc_legacy_large_radius_reverse` | 18x18 | 11 | 3 | 2 | exact |
| `16bpc_legacy_mixed_alpha_reverse` | 18x12 | 3 | 2 | 2 | exact |

The mixed-alpha fixture includes zero-alpha boundaries and interior holes plus
nonzero partial alpha words. Complete A/R/G/B buffers are compared byte-for-
byte against actual AEX output.

Replay:

```text
python3 tools/emulation/smoke_olmblur_worker16_legacy.py
```

The final replay result is three passing complete buffers with no mismatched
bytes.
