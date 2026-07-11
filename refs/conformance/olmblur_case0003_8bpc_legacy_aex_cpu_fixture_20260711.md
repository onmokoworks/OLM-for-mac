# OLMBlur 8bpc Legacy case0003 CPU fixture

Date: 2026-07-11

## Scope

This is a local complete-worker witness for the formal 960x540 case0003
residual. It uses the actual `plugins_2025/OLMBlur.aex` entry
`FUN_180007300` under Unicorn CPU emulation and does not use PNG tuning.
The synthetic geometry is 6x6 so the radius-248, repeat-10 worker completes
within the local AEX instruction budget while retaining an active red-only
interior gradient and a distinct outer boundary gradient.

Exact parameter block:

| bit depth | amount | smoothness | repeat | bias | Legacy |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 8 | 248.6 | 100 | 10 | 1 | 1 |

## AEX materialization

Command:

```text
python3 tools/emulation/test_olmblur_worker8_legacy.py --export
```

Observed AEX facts for the added case:

- worker: `0x180007300`
- binary SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- dimensions: `6x6` synthetic, formal case dimensions `960x540`
- instructions: `3624003` (below the `8000000` guard)
- PF callback count: `48`
- source SHA-256: `680c3cf7dffabc4d4527f3a3698bea01d3a7352786c47e2389891d8f3f19083e`
- expected AEX output SHA-256: `c72f434389bffe31e9164d8c23605657f33b2c421ece6f49b62074afa533a5d7`

## Portable replay

Command:

```text
python3 refs/scripts/smoke_olmblur_worker8_legacy.py
```

Output:

```text
PASS 8bpc_legacy_basic bytes=576
PASS 8bpc_legacy_large_radius_reverse bytes=1296
PASS 8bpc_legacy_mixed_alpha_reverse bytes=864
PASS 8bpc_legacy_case0003_radius248_boundary_gradient bytes=144
[OK] OLMBlur 8bpc Legacy worker matches 4 complete AEX fixtures, including case0003 radius248 boundary gradient
```

The added case is byte-exact through the portable Legacy core. Existing
radius-3/radius-11 fixtures remain exact. No Mac adapter, Xcode project, or
conformance ledger file was changed, and no core formula change was needed.
