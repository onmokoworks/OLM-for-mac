# OLMDirectionalBlur scatter boundary matrix

Date: 2026-07-15

Mac-only helper proof for the pending row755 typed witness. The test executes
the pinned `OLMDirectionalBlur.aex` scatter entry at `0x1800013e0` and the
current `core/dblur_rowdriver.cpp` helper over the same synthetic row. It does
not use PNG values and does not establish the complete DirectionalBlur path.

## FACT

- Forward `count=5`, `coefficient=1`, source `x=3`, width `7` reaches target
  columns `x=4..6`; the source column and row-end column remain unchanged.
- Backward `count=5`, `coefficient=1`, source `x=3`, width `7` reaches target
  columns `x=2..1`; the left boundary clips before `x=0`.
- Forward `count=5`, `coefficient=0.5` reaches only `x=4` and selects the
  weight-table index by truncating `i / coefficient`.
- `coefficient=0` performs no writes.
- In every case, the AEX and current helper produced the same tested output
  bytes as the float32 operation-order model; source, weights, the source
  column, and adjacent rows stayed unchanged.

## INFERENCE

- A future row755 typed destination, denominator, and alpha/valid export can
  discriminate helper coverage by checking changed cells against the recorded
  source column, direction, effective span, and row boundary. A PNG-only
  comparison cannot perform this check.
- This narrows the Windows question to helper-local coverage and side-channel
  ownership. It does not identify the complete render-path cause of any final
  image residual.

## Targeted command

```text
python3 tools/emulation/test_dblur_scatter_boundary_matrix_20260715.py
```

Observed result: all four matrix cases passed for both the pinned AEX helper
and the current core helper.
