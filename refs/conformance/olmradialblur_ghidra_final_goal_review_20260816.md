# Final goal audit — OLMRadialBlur Ghidra semantics

Date: 2026-08-16

## Decision: GO

The goal is complete at the defensible behavior-level standard:

> Every frozen OLMRadialBlur function start has a documented behavioral meaning, address, live Ghidra name, call/reference context, Mac mapping or explicit absence, evidence, and bounded confidence. Exact original C++ identifiers are not claimed where the binary does not support them.

## Final verified state

| Check | Result |
|---|---:|
| Frozen primary functions | **362/362** |
| Missing / extra / duplicate addresses | **0 / 0 / 0** |
| Master parse gaps | **0** |
| Master/live current-name equality | **362/362** |
| Live semantic names | **338/362** |
| Deliberate automatic-name exceptions | **24/362** |
| Safe pure-High operation names left automatic | **0** |
| Duplicate live names | **0** |
| Out-of-range registered callback function starts classified | **1/1** |
| Final live naming snapshot rows | **363** |

The official validator passes all 15 primary chunks and reports 362 rows exactly once. Confidence totals are 317 High, 36 Medium, 5 Low, 3 mixed High+Medium, and 1 mixed High+unknown. The one purpose-unknown row, `0x180001ab0`, has proven no-op behavior and bounded callers; only its stripped source-level purpose remains unclaimed.

## Acceptance conditions

### Live naming cleanup

The previously missing 21 pure-High operation names are applied. The codecvt thunk collision is resolved. The remaining 24 automatic names are deliberate confidence exceptions, each with a behavioral ledger row and evidence; no safe pure-High operation name remains unapplied. Eighteen Medium-confidence applied names are accepted as conservative operation/navigation labels whose remaining uncertainty is limited to suffix, owner, typedef, or template spelling.

### Canonical live-name master

The canonical inventory was rebuilt from a fresh live Ghidra function snapshot. It records literal live names, matches all 362 address/name pairs, has no duplicate current names, and contains no parse gaps.

### Indirect callback boundary

The AEGP Compute Cache registration table was closed. Exactly one registered callback function start lies outside the frozen primary range: `0x18001ce70 RadialBlur_ComputeCache_DestroyValue`. It is classified at High confidence and included in the inventory appendix. No other out-of-range registered function start was found at this boundary.

### Semantic corrections and supporting boundaries

Independent reviews verified the exported command switch through command 33, EffectBase/MyEffect vtables, direct and indirect callback roots, typed PF8/PF16/PF32 render owners, imported math leaves, UI/update behavior, dormant Ramp/Curve/String framework ownership, and Mac counterparts or explicit absence. All previously reported P1/P2 semantic inconsistencies were corrected.

## Boundary

This is complete behavioral classification of the frozen binary function set. It is not a claim that stripped original C++ symbol spellings were recovered, nor that every arbitrary input and parameter combination is numerically identical across Windows and macOS.

**Final semantic status: GO. No remaining P0/P1/P2 blocker.**
