# OLMBlur 8bpc Legacy Complete Worker

Date: 2026-07-11

## Scope

This artifact is the portable `FUN_180007300` worker slice. It uses the
already accepted exact `FUN_1800014f0` / `FUN_180001ea0` helper core and does
not modify that core, the existing helpers, Mac code, ledger, or NAS files.

## Grounded behavior

- Stages little-endian A,R,G,B input into an RGB float plane plus an alpha
  validity plane, retaining the copied alpha byte on output.
- Uses the fixed render-scaled Legacy radius, smoothness-derived sigma, and
  symmetric `FUN_180009e10` weights with center weight `1.0`.
- Performs six horizontal and six vertical subpasses per repeat, swapping the
  two RGB planes in the AEX call order for Bias Direction `1` or `2`.
- Writes 8bpc RGB as `floorf(value + 0.5f)` from the final AEX float plane.

## Fixture gate

The actual AEX is pinned to SHA-256
`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b` and the
worker entry is `0x180007300`. The fixture manifest is
`tools/emulation/fixtures/olmblur_worker8_legacy/manifest.json`.

Proven complete-buffer cases:

| Case | Size | Radius | Repeat | Bias | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| `8bpc_legacy_basic` | 12x12 | 3 | 2 | 1 | exact |
| `8bpc_legacy_large_radius_reverse` | 18x18 | 11 | 3 | 2 | exact |
| `8bpc_legacy_mixed_alpha_reverse` | 18x12 | 3 | 2 | 2 | exact |

The mixed-alpha source has zero-alpha outer boundaries plus interior holes
(`zero_alpha_count=69`) and nonzero partial alpha values `32, 96, 160, 224`.
Those values all enter the AEX validity plane as active, while zero alpha
exercises the Legacy `0x14f0` copy and `0x1ea0` untouched branches across all
six chunk calls in both directional passes.

Replay:

```text
python3 refs/scripts/smoke_olmblur_worker8_legacy.py
```

The fixtures use actual A/R/G/B staging. The two varying-RGB cases cover the
worker arithmetic and writer, while the mixed-alpha case covers validity-state
branching and reverse orchestration. No writer or helper rule is inferred from
PNG output.
