# OLMSmoother2 case0012 natural post-f130 boundary - 2026-07-18

- Verdict: `PASS_BOUNDED_NATURAL_ACTUAL_AEX_POST_F130_AND_CCE0_INPUT`
- Scope: bounded Mac-local Unicorn execution of the checked-in current Windows AEX.

## FACT

- Host-translated descriptor: `[92, 841, 1, 92, 842, 2]`; dispatch key `20`.
- Post-f130 polygon count: `2`.
- Post-boost polygon count: `2`.
- The post-boost builder polygon and compact cce0 input are bitwise equal, including float32 words.
- cce0 output float4: `[0.8575195670127869, 0.8575195670127869, 0.8575195670127869, 0.9387068152427673]`.

## Natural Chain

`PF8 host adapter -> 0x180002a70 -> 0x180002ba0 -> 0x18000ada0 -> VCOMP140!_vcomp_fork -> 0x18000ac00 -> 0x18000ae10 -> 0x18000cce0 -> 0x18000c280 -> 0x18000fef0 -> 0x18000f270 -> 0x18000f130`

The PF8 host boundary is adapted with `(channel * alpha + 127) // 255`. Key removal, sRGB decode, class-plane generation, c280 dispatch, f270/f130, and cce0 execute from the actual AEX.

## Boundary

- The imported Windows `pow` is currently implemented by Mac libm. At the retained `(92,840)` sample, its red float differs from the Windows retained value by `3` float32 ULPs.
- Therefore this closes local execution reachability and polygon ownership, not Windows/AE byte exactness.

## Reproduction

```sh
python3 tools/emulation/run_olmsmoother2_case0012_natural_post_f130_20260718.py
```

## Claims Not Made

- No Mac plug-in source change.
- No Windows package change.
- No AE exactness or final writer exactness claim.
