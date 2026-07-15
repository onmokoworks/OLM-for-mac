# OLMBlur case_0006 bounded border/order/writer differential

This standalone Mac actual-AEX/portable fixture does not modify existing 20260716 blur differentials or the ledger.

- AEX SHA-256: `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Entry: `0x180002280`
- Actual-AEX runs: 3 bounded fixtures; no AE exact claim.

## Results

- `border_radius4_opaque` [7, 5]: baseline equal=`False`, reverse-order equal=`False`, replicated-border equal=`False`, nearest-even equal=`False`.
- `order_radius5_high_dynamic_range` [9, 7]: baseline equal=`True`, reverse-order equal=`True`, replicated-border equal=`False`, nearest-even equal=`True`.
- `writer_near_half_inputs` [5, 5]: baseline equal=`True`, reverse-order equal=`True`, replicated-border equal=`False`, nearest-even equal=`False`.

## Interpretation

- Border: **not excluded**. The opaque radius-4 probe disagrees with both the portable truncated-edge candidate and the replicated-edge candidate; this fixture isolates the boundary family but does not identify its exact AEX rule.
- Coefficient accumulation order: **not excluded**. The tested reverse traversal did not produce a quantized output difference in the order-focused cases, so this fixture cannot decide all reassociation variants.
- Final writer rounding: **excluded as the final PF16 writer rule** by the existing actual-AEX half-tie microtest and the near-half worker probe. No global writer change is justified.
- These results are local binary/portable evidence only; they do not establish AE exactness or explain the one-pixel Mac export residual.

## Commands

`python3 tools/emulation/test_olmblur_case0006_border_order_writer_differential_20260716.py`
