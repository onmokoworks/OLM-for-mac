# OLMKiraKira Merge Mode plumbing - 2026-07-16

- Status: `HOST_PARAMETER_PLUMBING_FIXED`
- Correctness promotion: none
- Mode 2 execution: guarded

## Fact

The AE parameter surface already exposed `Merge Mode`, but the Mac render info
structure, normal render parameter read, and Smart Render checkout omitted it.
The Mac path therefore had no way to distinguish the two UI values.

The bounded fix adds `merge_mode` to `OLMKiraKiraInfo` and populates it from
`OLMKIRAKIRA_MERGE_MODE` in both `ReadRenderInfo` and `CheckoutSmartInfo`.
The Smart path checks the parameter back in normally.

The binary evidence identifies distinct aggregation targets:

- Mode 1: `FUN_18114fd90`
- Mode 2: `FUN_18114ffd0`

Mode 2's inner five-ray accumulation, threshold `0.001`, four clamps, and
post-clamp float stores are grounded. Its later host compose and selected
typed writer are not yet uniquely bound. This change therefore does not alter
`RenderTyped` or claim that Mode 2 renders correctly.

## Verification

```text
python3 tools/emulation/test_olmkirakira_merge_mode_plumbing_20260716.py
PASS normal_merge_mode=1 smart_merge_mode=2 checks=8/8 execution=guarded
```

A no-install Debug Xcode build also succeeded for the universal arm64+x86_64
bundle. This is a host-surface repair, not `AE exact` evidence.
