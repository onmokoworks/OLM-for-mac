# OLMSmoother2 Legacy Lane State - 2026-07-03

- Feature: `legacy current-AEX key/gamma residuals`
- Status: `writer-confirmed-internal-branch-unresolved`
- Decision: `runtime-or-asm-first-divergence-required`
- Recommended action: Anchor the next local/Windows trace-diff harness at the confirmed writer frame, then capture only the listed producer fields until the first c280/cce0 divergence is observed.
- Safe claim: final writer bytes/floats are already grounded for the active legacy witnesses; the unresolved lane is the first producer divergence feeding c280/cce0, not PNG export or final u8 packing.
- Latest Windows return: `olmsmoother2_current_aex_writer_frame_followup_trace_20260625` / `answered_partial`
- Return summary: Writer-anchored follow-up captured exact OLMSmoother2+0x3610 final writes for both requested pixels and the writer-frame local result block. Case 0004 has x=0x76f,y=0x207 and floats 0.80824906/0.80824906/0.80824906/0.44156867. Case 0012 has x=0x5b,y=0x349 and floats 1/1/1/0 with final raw 0xffffff00. The exact producer inside c280/helper append remains unisolated.

## legacy_case_0004_current_aex

- Witness: `(1903,519)`
- Reference / local: `[103, 103, 103, 113]` vs `[0, 0, 0, 0]`
- Local path: `local-transparent-center-no-polygon-passthrough`
- Static dispatch: `{'dispatch': 'FUN_180013140', 'hex': '0xd0', 'idx': 208, 'required_windows_fields': ['c280 switch index at exact writer-frame pixel', 'polygon vertex count before bb10/b120', 'helper append src xy / rgba / weight if any', 'cce0 output floats before final u8 packing'], 'unresolved_stage': 'c280-polygon-or-cce0-fallback'}`
- First unresolved stage: `c280-polygon-or-cce0-fallback`
- Stop line: Do not add a global transparent-center fallback. This witness only proves a 0004-local path if cce0/c280 emits a neighbor sample for the same call.

### Required Windows Fields

- c280 switch index at exact writer-frame pixel
- polygon vertex count before bb10/b120
- helper append src xy / rgba / weight if any
- cce0 output floats before final u8 packing

## legacy_case_0012_gamma5_red_blue_current_aex

- Witness: `(91,841)`
- Reference / local: `[0, 0, 0, 0]` vs `[90, 90, 90, 91]`
- Local path: `local-cardinal6-f270-e3a0-append`
- Static dispatch: `{'dispatch': 'FUN_1800125c0 -> FUN_180010760 -> FUN_18000cc70', 'hex': '0x69', 'idx': 105, 'required_windows_fields': ['c280 switch index at exact writer-frame pixel', 'cardinal6 descriptor/key and polygon count before append', 'e170 bits/code plus f270/e3a0 append/no-append', 'cce0 output floats before final u8 packing'], 'unresolved_stage': 'cardinal6-e170-f270-e3a0-emit-chain'}`
- First unresolved stage: `cardinal6-e170-f270-e3a0-emit-chain`
- Stop line: Do not suppress f270 or transparent-center appends globally. Prior probes show global f270 suppression worsens the case set.

### Required Windows Fields

- c280 switch index at exact writer-frame pixel
- cardinal6 descriptor/key and polygon count before append
- e170 bits/code plus f270/e3a0 append/no-append
- cce0 output floats before final u8 packing

## Global Rejections

- `curve_idx`: rejected-inert
- `f270_suppression`: rejected-worse
- `transparent_center_fallback`: rejected-without-local-cce0-c280-proof

## Inputs

- producer_diff_json: `refs/conformance/olmsmoother2_producer_path_diff_20260702.json`
- decision_json: `refs/conformance/olmsmoother2_current_aex_8bpc_decision.json`