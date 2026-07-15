# OLMDirectionalBlur Angle-0 vs Diagonal Schedule Proof

## Status

- `pass`, local actual-AEX schedule differential.
- The fixture intentionally stops at `0x180005554` after rowdriver scheduling; no final image or AE-exact claim is made.
- No production file, existing fixture, ledger, Windows package, or NAS archive was changed.

## Evidence

- AEX: `plugins_2025/OLMDirectionalBlur.aex`
- AEX SHA-256: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`
- Source fixture: `refs/win_references/20260604_olm/OLMDirectionalBlur/case_0001_before_effects.png`
- Fixture SHA-256: `e3216aa5a213efaf2129dd11bf9c4a5e6e4a5c162d034c607df6e0bda1fba80a`

| control angle | materialized rotate angle | bits | dimensions | Iterate8 area | rowdriver calls | stop |
| ---: | ---: | --- | --- | --- | ---: | --- |
| 0 deg | 1.5707963705 rad (90.000003 deg) | `0x3fc90fdb` | `[26, 26]` | `[0, 0, 16, 16]` | 26 | `0x180005554` |
| 45 deg | 2.3561944962 rad (135.000000 deg) | `0x4016cbe4` | `[26, 26]` | `[0, 0, 16, 16]` | 26 | `0x180005554` |

## Proof

- User angle 0 does not bypass rotation or mean a zero-angle rotate call: the actual AEX passes `pi/2` to `FUN_180001ec0`.
- User angle 45 changes the same rotate argument to `3pi/4`; the AEX still uses the same rotate invocation, PF Iterate8 area, and 26 rowdriver chunks.
- Therefore the next semantic split is the rotate angle/value path (`pi/2` axis-aligned versus `3pi/4` diagonal), not host-world rectangle mapping or an angle-0 rotate bypass.
- This does not prove Mac AE host binding, rotated sampler validity, normalization, final writeback, or production integration.

## Reproduction

```sh
python3 tools/emulation/test_dblur_angle0_diagonal_schedule_20260716.py
```
