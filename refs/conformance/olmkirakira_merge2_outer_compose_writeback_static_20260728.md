# OLMKiraKira Merge2 outer compose/writeback static contract

Date: 2026-07-28
Status: binary-grounded / static
AE exact: false

## Result

The post-`FUN_18114ffd0` consumer is present in the pinned AEX. The three
bit-depth owner lanes call `FUN_18114f4a0`, stage its interleaved float RGBA
Mat, then call a depth-specific outer compose loop:

| Depth | owner call to ray driver | outer compose | writer calls |
| --- | --- | --- | --- |
| PF16 | `0x18114d05c` | `FUN_18114ddc0` | `FUN_181230bd0` |
| PF8 | `0x18114d62c` | `FUN_18114e110` | `FUN_181230b90` at `0x18114e287`, `0x18114e3e9` |
| PF32 | `0x18114dbfc` | `FUN_18114e460` | `FUN_181230c20` at `0x18114e5d7`, `0x18114e739` |

The owner state at `+0x44` selects the outer formula. Value `1` takes the
branch containing `DIVSS`; value `2` takes the direct weighted-sum branch.
This is the same Merge Mode parameter checked out at `FUN_18114e860` selector
`0x11`. It is not a later depth/writer selector.

## Buffer and formula contract

- Both inputs are interleaved float32 RGBA. The loops read channel offsets
  `+0,+4,+8,+0xc` and advance each input by `0x10` bytes per pixel.
- Glow is the owner pointer at `+0x190`; source is the owner pointer at
  `+0x128`. Each alpha is multiplied by Glow Opacity (`+0x38`) or Source
  Opacity (`+0x3c`) and independently clamped by `FUN_181156740`.
- A zero test is performed on the unscaled input-alpha sum. If it is zero,
  all four output channels are zero.
- Outer mode 1 computes opacity-weighted RGB, divides RGB by the sum of the
  two scaled alphas, and clamps RGB and summed alpha independently.
- Outer mode 2 computes the same opacity-weighted RGB sums but does **not**
  divide RGB by alpha; it clamps RGB and summed alpha independently.
- There is no screen blend in these three compose functions (`SUBSS` is
  absent). Source alpha is not passed through unchanged.

Immediately before each typed writer call, the compose result is arranged as
R/G/B/A in `XMM0/XMM1/XMM2/XMM3`; destination is stack argument 5
`[RSP+0x20]`. The already-proven leaf writers store ARGB: PF8/PF16 scale by
255/32768 and truncate toward zero, while PF32 stores float bits.

## Production compatibility and bounded gate

The current Mac production path is incompatible with both binary outer modes:
it always uses screen RGB, normalizes the Merge1 glow earlier, and passes
source alpha through. A safe Merge2 integration must therefore be gated on:

1. separate inner aggregation dispatch (`+0x08` vs `+0x10`);
2. retention of uncomposed source and interleaved glow RGBA buffers;
3. the outer `merge_mode` branch above, after Glow/Source Opacity;
4. depth-specific writer conformance, including truncation rather than a
   generic rounded conversion;
5. one same-pixel runtime witness at the outer mode-2 writer call to confirm
   owner pointer identity and rule out a host wrapper/path split.

No production or ledger file was changed.

## Verification

`python3 tests/test_olmkirakira_merge2_outer_compose_static_20260728.py`
