# OLMKiraKira Merge-Mode-2 Address Contract

Date: 2026-07-16
Status: **pass**
Evidence class: **Mac-only static binary evidence plus independent float32 model**

## Result

The pinned decomp and disassembly agree that the Merge-Mode-2 vtable target is
`FUN_18114ffd0 @ 0x18114ffd0`, distinct from the Merge-Mode-1 target
`FUN_18114fd90`. The bounded target contract is:

- clear the output RGBA float buffer;
- process five ray layers per pixel;
- skip a ray when it is at or below `DAT_181489990`;
- add the selected layer RGB directly, without the Mode-1 alpha multiplier;
- add the raw ray value to output alpha;
- clamp R, G, B, and A independently through
  `FUN_181156740 @ 0x181156740`.

The local regression passes `11/11` static checks and `4/4` model checks. The
model is an independent float32 replay of the observed operation order, not a
second binary oracle.

## Boundary

This narrows the merge-mode-2 aggregation target, but it does **not** prove the
later source/glow composition formula, UI naming, host binding, Windows AE
output, or AE exactness. It does not justify a production change or PNG tuning.
The numeric value of `DAT_181489990` is intentionally left unresolved; the
model uses an explicit test epsilon only to exercise the observed branch.

## Exact Next Witness

Prepare one Software render with a short nonzero ray, a zero-ray control, and a
five-active-ray saturation case. In one same-run trace, bind the AEX hash,
module base, and vtable target at `0x18114ffd0`; capture the output address at
the `0x181150250` zero-fill; capture one ray/color pair at `0x181150080`; then
capture pre-clamp RGBA at `0x181150112` and all four
`0x181156740` input/return pairs. Accept only the same-run raw float contract.
Final PNG bytes remain non-authoritative.

## Reproduction

```sh
python3 scripts/prove_olmkirakira_merge2_address_contract_20260716.py
python3 tools/emulation/test_olmkirakira_merge2_address_contract_20260716.py
```
