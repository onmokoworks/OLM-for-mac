# OLMToonDilate PF32 Seed Propagation Matrix - 2026-07-17

## Result

- Status: **PASS_PF32_SEED_PROPAGATION_MATRIX**
- AEX: `aex/OLMToonDilate/Plugins/64/2025/OLMToonDilate.aex`
- Worker/helper: `0x1801a6800` / `0x1801ac8e0`
- Scope: 48 independent actual-worker runs: 8 directions x 3 alpha values x 2 radii.
- Execution: checked-in AEX under local Unicorn; output read immediately after worker return.

## FACT

- Seed directions cover left, right, up, down, and all four diagonals.
- Semi-alpha values are 0.499, 0.5, and 0.501; radii are 1 and 2.
- The independent oracle copies raw PF32 A,R,G,B words through an 8-neighbor BFS.
- Every case requires exact visible 4-word equality and all four bytes of every row padding sentinel.
- Gates: `{"aex_present": true, "aex_sha256": "c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3", "all_helpers_observed": true, "all_row_padding_preserved": true, "all_visible_4_word_exact": true, "all_workers_returned": true, "case_count_48": true}`

## Boundary

- This report is bounded Mac-local binary/Unicorn evidence only.
- It makes no After Effects exactness or Windows exactness claim.
- It does not modify production code or the existing witness.

## Reproduce

```sh
tools/emulation/.venv/bin/python tools/emulation/test_olmtoondilate_pf32_seed_propagation_matrix_20260717.py
```
