# OLMSmoother2 Producer-Path Diff

- Decision: `writer-anchored-producer-trace-ready`
- Recommended action: Anchor the next local/Windows trace-diff harness at the confirmed writer frame, then capture only the listed producer fields until the first c280/cce0 divergence is observed.

## Summary

| Case | XY | Local path | Static dispatch | First unresolved stage |
| --- | --- | --- | --- | --- |
| `legacy_case_0004_current_aex` | `[1903, 519]` | `local-transparent-center-no-polygon-passthrough` | `0xd0 -> FUN_180013140` | `c280-polygon-or-cce0-fallback` |
| `legacy_case_0012_gamma5_red_blue_current_aex` | `[91, 841]` | `local-cardinal6-f270-e3a0-append` | `0x69 -> FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70` | `cardinal6-e170-f270-e3a0-emit-chain` |

## legacy_case_0004_current_aex

- Witness xy: `[1903, 519]`
- Reference RGBA: `[103, 103, 103, 113]`
- Local candidate RGBA: `[0, 0, 0, 0]`
- Windows writer anchor: raw `0xe8e8e871`, float `[0.80824906, 0.80824906, 0.80824906, 0.44156867]`, explains reference `True`
- Local producer shape: `empty polygon -> transparent passthrough`
- Stop line: Do not add a global transparent-center fallback. This witness only proves a 0004-local path if cce0/c280 emits a neighbor sample for the same call.

### Stage Matrix

| Stage | Local checkpoint | Windows checkpoint | Status | Note |
| --- | --- | --- | --- | --- |
| `writer-anchor` | `[0, 0, 0, 0]` | `[103, 103, 103, 113]` | `satisfied` | Windows raw 0xe8e8e871 already explains reference PNG. |
| `cce0-result` | `1.00000000,1.00000000,1.00000000,0.00000000` | `[0.80824906, 0.80824906, 0.80824906, 0.44156867]` | `unresolved` | Writer frame contains post-cce0 local result block, but the exact producer into that block is not isolated. |
| `c280-dispatch` | `{"dispatch": "FUN_180013140", "hex": "0xd0", "idx": "208"}` | `unknown` | `unresolved` | Expected local dispatch shape for legacy_case_0004_current_aex. |
| `producer-branch` | `{"passthrough": "1.00000000,1.00000000,1.00000000,0.00000000", "polygon_count": "0"}` | `unknown` | `unresolved` | Need to learn whether Windows also has zero vertices or appends a neighbor-derived sample before cce0. |

### Required Windows Fields

- c280 switch index at exact writer-frame pixel
- polygon vertex count before bb10/b120
- helper append src xy / rgba / weight if any
- cce0 output floats before final u8 packing

## legacy_case_0012_gamma5_red_blue_current_aex

- Witness xy: `[91, 841]`
- Reference RGBA: `[0, 0, 0, 0]`
- Local candidate RGBA: `[90, 90, 90, 91]`
- Windows writer anchor: raw `0xffffff00`, float `[1.0, 1.0, 1.0, 0.0]`, explains reference `True`
- Local producer shape: `cardinal6 append -> nonzero cce0 blend`
- Stop line: Do not suppress f270 or transparent-center appends globally. Prior probes show global f270 suppression worsens the case set.

### Stage Matrix

| Stage | Local checkpoint | Windows checkpoint | Status | Note |
| --- | --- | --- | --- | --- |
| `writer-anchor` | `[90, 90, 90, 91]` | `[0, 0, 0, 0]` | `satisfied` | Windows raw 0xffffff00 already explains reference PNG. |
| `cce0-result` | `0.99106723,0.99106723,0.99106723,0.35492450` | `[1.0, 1.0, 1.0, 0.0]` | `unresolved` | Writer frame contains post-cce0 local result block, but the exact producer into that block is not isolated. |
| `c280-dispatch` | `{"dispatch": "FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70", "hex": "0x69", "idx": "105"}` | `unknown` | `unresolved` | Expected local dispatch shape for legacy_case_0012_gamma5_red_blue_current_aex. |
| `producer-branch` | `{"append": {"dst": "91,841", "rgba": "0.99106717,0.99106717,0.99106717,0.99607843", "src": "91,840", "weight": "0.35632184"}, "cardinal6": {"count_before": "0", "desc": "91,841,1,91,843,5", "key": "50"}, "e170": {"a_center": "0", "a_prev": "1", "c": "2", "desc": "91,841,1,91,843,5", "r_left": "0"}, "e3a0": {"desc": "91,841,1,91,843,5", "scale_h": "1", "scale_m": "0.57999998", "trap": "1.74,0,0.5", "weight": "0.35632184"}, "f270": {"c": "2", "count_before": "0", "extra_n": "0.40000001", "p3": "1"}}` | `unknown` | `unresolved` | Need the first Windows-vs-local difference inside the cardinal6/e170/f270/e3a0 chain. |

### Required Windows Fields

- c280 switch index at exact writer-frame pixel
- cardinal6 descriptor/key and polygon count before append
- e170 bits/code plus f270/e3a0 append/no-append
- cce0 output floats before final u8 packing