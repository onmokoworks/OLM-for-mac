# OLMBlur 8/16bpc max=1 residual family (2026-07-18)

## New bounded fact

The radius-1 interior/order fixture is exact under the current C++ model and its reversed accumulation variant, but the radius-1 edge fixture is not exact and exposes out-of-range PF16 words; therefore the 8/16bpc max=1 family is not classified as a final-writer-only issue and border/helper state remains live.

## Evidence

- Actual AEX: `plugins_2025/OLMBlur.aex` SHA-256 `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`.
- AEX/decomp and current C++ both retain the add-half/floor writer contract.
- The retained 8bpc witness is `(488,941)`, pre-store `250.499985`; the retained 16bpc witness is `(345,672)`, pre-store blue `12544.5`.
- At radius 1, the interior/order actual-AEX output equals both the current C++ model and reversed accumulation model.
- At radius 1, the edge actual-AEX output differs from the truncated-edge C++ model and includes out-of-range PF16 words in the bounded synthetic world.

## Classification

- Coefficient: not implicated by the interior/order equality in this bounded probe.
- Accumulation order: not implicated by the tested reversal.
- Final writeback: not sufficient to explain the family; both retained witnesses straddle different pre-store conditions.
- Border/helper: remains the live candidate, without an exact rule identified.

## Boundary

Mac-only, actual-AEX/portable fixture evidence. No Windows work, no plugin/source change, and no AE-exact promotion.

## Reproduce

`python3 tools/emulation/test_olmblur_8_16bpc_max1_residual_family_20260718.py`
