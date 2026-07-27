# OLMSmoother2 case-09 32bpc Mac AE exact (2026-07-27)

The declared no-key `final_random10_olm_smoother_v2_09` slice is `AE exact`.
Windows and Mac AE `26.3x87` used the same hash-bound Preserve RGB source,
Software renderer, 32bpc project, working space `None`, disabled linear
blending, and uncompressed FLOAT RGBA EXR contract.

The final diagnostic-free Mac binary is
`c14bb3424b8b8ce58d09fe372a443f844319d18fec5db5ef1cfc1019e3e839eb`
and was built at the pinned `-O2` optimization level.

| Gate | Compared words | Mismatches | Max raw u32 delta |
| --- | ---: | ---: | ---: |
| Windows vs Mac no-effect control | 8,294,400 | 0 | 0 |
| Windows vs Mac effect-on | 8,294,400 | 0 | 0 |

## Binary-grounded correction

The initial effect comparison had 14,927 mismatched channel words with a
maximum raw-u32 delta of 8, always in the Mac-high direction. Actual-AEX
runtime tracing localized a real reciprocal-rounding divergence in
`FUN_18000c0d0`.

Windows computes the gamma exponent with scalar float32 `DIVSS`
(`1.0f / gamma`) and only then promotes the rounded value with `CVTPS2PD`
for the imported `pow` calls. The Mac source previously divided in binary64.
The port now preserves the AEX sequence:

```cpp
const float exponent_f = K_ONE / gamma_value;
const double e = (double)exponent_f;
```

At witness `(723,0)`, the corrected Mac AE runtime stages are:

- after c0d0 RGBA words:
  `[1025415550,1051983194,1035888241,1065353216]`
- after ab00 RGBA words:
  `[1041251506,1053915028,1035490902,1065353216]`
- cce0 RGBA words:
  `[1018784351,1043726452,1008471117,1065353216]`
- final PF32 ARGB words:
  `[1065353216,1042713209,1055576803,1036394430]`

The runtime route was PF32 with full-frame input/output worlds:
`1920x1080`, `rowbytes=30720`, extent `[0,0,1920,1080]`.

## AE cache control and regression

After replacing the plug-in, AE initially returned the old frame without
entering `RenderBits`. No Adobe preference or cache was changed. Copying the
hash-identical input to a fresh path changed only the footage identity and
forced a real render. The same method was used for the diagnostic-free final
proof.

The final binary was then regressed through the complete frozen 8bpc
current-AEX legacy/key/gamma request using a fresh request-tree path:
`12/12`, `max_diff=0`.

Machine-readable evidence is
`refs/conformance/olmsmoother2_case09_32bpc_mac_ae_exact_20260727.json`.
This promotes only the declared 32bpc case-09 slice; other untested 32bpc
cases remain unpromoted.
