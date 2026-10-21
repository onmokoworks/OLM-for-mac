# OLMRadialBlur live Ghidra naming policy and final adjudication

Date: 2026-08-16  
Target: live Ghidra MCP `default`  
Scope: the frozen 362 function starts in `[0x180001000,0x18001ce70)`, plus the r16 out-of-range callback closure. No production source was edited and the target was not switched.

## Policy

1. A function receives a semantic live name when its operation/ownership is High confidence from decompile, call graph, vtable/RTTI, constants, or registration-table evidence.
2. Names describe the narrowest proven operation. They need not reconstruct the original C++ identifier.
3. Medium/Low canonical identity remains automatic unless a conservative operation-only name was already useful and its uncertain component is explicitly bounded here.
4. `_A`/`_B`/`_E`, `Mask`, `Buffer`, and `RenderContext` are binary/call-site disambiguators, not claims about recovered template spelling.
5. ABI thunks must have distinct `thunk_` names; behaviorally identical entries must not share the same live name.

## High-confidence names applied in this pass

| Address | Live name |
|---:|---|
| `0x18000f1d0` | `EffectBase_CheckoutWStringPayloadAt18` |
| `0x18000f580` | `EffectBase_QueryPointParamViaSuite` |
| `0x18000f7c0` | `RadialBlur_RegisterComputeCacheCallbacks` |
| `0x18000fb20` | `EffectBase_NormalizeCustomUIEventCoords` |
| `0x18000fff0` | `AErrException_DeletingDestructor` |
| `0x180010030` | `ErrException_DeletingDestructor` |
| `0x180010070` | `StdException_DeletingDestructor` |
| `0x180010f00` | `DRAWBOT_Exception_DeletingDestructor` |
| `0x180016690` | `thunk_codecvt_utf8_utf16_do_length` |
| `0x180017ee0` | `PFWorldOwner_InitAllocate` |
| `0x180018030` | `PFWorldOwner_CleanupThunk` |
| `0x180018050` | `PFWorldOwner_ResetAllocate` |
| `0x180018230` | `PFWorldOwner_Allocate` |
| `0x18001c0f0` | `CurveDataHandler_ArbInterpolate` |
| `0x18001c540` | `StringDataHandler_ArbNew` |
| `0x18001c630` | `StringDataHandler_ArbCopy` |
| `0x18001c790` | `StringDataHandler_ArbFlatten` |
| `0x18001c8d0` | `StringDataHandler_ArbUnflatten` |
| `0x18001ca10` | `StringDataHandler_ArbFlatSize` |
| `0x18001ca20` | `StringDataHandler_ArbCompare` |
| `0x18001cc80` | `StringDataHandler_ArbInterpolate` |

The thunk rename removes the prior duplicate `codecvt_utf8_utf16_do_length` name. The live frozen set now has no duplicate function names.

## The 18 medium-confidence applied names: accepted conservative exceptions

All 18 are retained unchanged. Their base operation is directly proven; only the source-level owner, overload typedef, or specialization suffix is inferred. The qualifiers below are the binding interpretation of the live name.

| Address | Live name | Accepted interpretation / bounded uncertainty |
|---:|---|---|
| `0x180003070` | `RadialBlur_ReleaseSuiteLease` | Conditional suite release is exact; original RAII wrapper class name is unknown. |
| `0x180004280` | `RadialBlur_LockHandle_Mask` | Handle lock is exact; `Mask` is the role of its paired callers/allocator, not a recovered template name. |
| `0x180004320` | `RadialBlur_LockHandle_RenderContext` | Handle lock is exact; `RenderContext` is call-site ownership. |
| `0x1800043c0` | `RadialBlur_LockHandle_Buffer` | Handle lock is exact; `Buffer` intentionally avoids a stronger element-type claim. |
| `0x180004460` | `RadialBlur_NewHandle_BytesMask` | Byte-count allocation is exact; `Mask` is inferred from paired use. |
| `0x180004500` | `RadialBlur_NewHandle_BytesContext` | Byte-count allocation is exact; `Context` is inferred from typed owner pairing. |
| `0x18000d970` | `EffectBase_RegisterCustomUI` | Registration operation is exact; exact SDK descriptor/type spelling is unknown. |
| `0x18000dab0` | `EffectBase_CheckoutColorFloat_A` | Color-float checkout is exact; `_A` is only a binary overload discriminator. |
| `0x18000db90` | `EffectBase_CheckoutColorFloat_B` | Same; `_B` does not claim source overload order. |
| `0x18000df70` | `EffectBase_CheckoutPoint3DScaled_A` | Three-value scaled checkout exact; public typedef and overload spelling unknown. |
| `0x18000e080` | `EffectBase_CheckoutPoint3DScaled_B` | Same; `_B` is an address-distinguishing suffix. |
| `0x18000e350` | `EffectBase_CheckoutScalar32_B` | 32-bit scalar extraction exact; underlying typedef unknown. |
| `0x18000e510` | `EffectBase_CheckoutFloatFromDouble_B` | Double-to-float extraction exact; source overload spelling unknown. |
| `0x18000e890` | `EffectBase_CheckoutScalar32_E` | 32-bit scalar extraction exact; `_E` is a stable binary discriminator only. |
| `0x18000e970` | `EffectBase_CheckoutFixed16_16ToFloat_B` | Fixed16.16 conversion exact; source typedef/overload spelling unknown. |
| `0x18000ea50` | `EffectBase_CheckoutHandlePayloadAt10_A` | Handle payload offset and checkout exact; concrete arbitrary-data class unknown. |
| `0x18000ec40` | `EffectBase_CheckoutHandlePayloadAt10_B` | Same; `_B` is a binary discriminator. |
| `0x18000ee30` | `EffectBase_CheckoutHandlePayloadAt138` | Offset-`+0x138` payload copy exact; concrete custom-data class unknown. |

These are policy exceptions rather than High-confidence canonical-source reconstructions. They are safe for navigation because every uncertain component is explicitly qualified and none changes behavioral classification.

## Remaining automatic names

Fresh live enumeration reports **24 automatic names out of 362 frozen functions**:

```text
180009360 180009370
18000c1b0 18000c220
18000f4c0 18000f5e0 18000ff40
1800154c0 180015f20 180016030
180019070 180019130 180019160 180019220 1800195f0 180019700 180019f20
18001a170 18001a290 18001a2a0
18001a540 18001a550 18001a560
18001c3c0
```

These are deliberate exceptions:

- Low behavior/source identity: `0x180009360`, `0x180009370`, `0x18001a540`, `0x18001a550`, `0x18001a560`.
- Medium canonical identity or generic wrapper specialization: the remaining 18 ordinary `FUN_...` entries through `0x18001a2a0`.
- High semantic role but only Medium canonical name: `0x18001c3c0`, the StringDataHandler state/default-definition initializer.

There is no remaining pure-High semantic row with a safe canonical operation name that was intentionally skipped. Automatic names are therefore bounded exceptions, not unfinished analysis.

## Live snapshot result

- Frozen function starts: **362**
- Automatic names: **24**
- Non-automatic names: **338**
- Duplicate live names: **0**
- Out-of-range callback renamed: `0x18001ce70 RadialBlur_ComputeCache_DestroyValue`

This snapshot supersedes the older `naming_audit.md` count of 66.
