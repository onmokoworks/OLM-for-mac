# OLMDistanceGradation PF16 max-2 compose sweep

Date: 2026-07-13

## Result

`PASS`: 12 bounded calls into the actual 2025 Windows AEX
`FUN_181170480` completed, covering the four representative field words at
`n-1`, `n`, and `n+1`. The runner reused the existing local exact-address
witness/world helpers.

| Case | XY | n | AEX output AGRB at n-1 | at n | at n+1 | transitions n-1->n / n->n+1 |
| --- | --- | ---: | --- | --- | --- | --- |
| 0024 | `(6,40)` | 3989 | `[32768,0,5430,28662]` | `[32768,0,5431,28661]` | `[32768,0,5431,28661]` | `[0,0,1,-1]` / `[0,0,0,0]` |
| 0025 | `(901,394)` | 7774 | `[32768,0,18560,14895]` | `[32768,0,18560,14896]` | `[32768,0,18559,14897]` | `[0,0,0,1]` / `[0,0,-1,1]` |
| 0026 | `(907,222)` | 25680 | `[32768,0,9908,23967]` | `[32768,0,9907,23968]` | `[32768,0,9906,23968]` | `[0,0,-1,1]` / `[0,0,-1,0]` |
| 0027 | `(1234,443)` | 30473 | `[32768,0,32768,0]` | `[32768,0,32768,0]` | `[32768,0,32768,0]` | `[0,0,0,0]` / `[0,0,0,0]` |

The JSON records each row's field/source words, local addresses, instruction
count, UI threshold parameters, and whether actual output words transitioned
across the neighborhood. UI thresholds are distance-domain values, so the
runner does not invent a PF16-word conversion for them.

## case_0026 Store Quantization

The four retained Mac PF16 store witnesses were mechanically recalculated
using `floor(word*255/32768)`, round-half-up `round(word/128)`, and
`truncate(word/128)`. The retained witness classification is `3/4
export-quantization`; the only retained unresolved point is `(907,222)`.

| XY | Mac PF16 store RGBA | Windows RGBA8 | floor RGB | round RGB | truncate RGB | retained class |
| --- | --- | --- | --- | --- | --- | --- |
| `(907,222)` | `[32645,0,129,65535]` | `[255,0,0,255]` | `[254,0,1]` | `[255,0,1]` | `[255,0,1]` | unresolved |
| `(395,477)` | `[32513,0,268,65535]` | `[253,0,2,255]` | `[253,0,2]` | `[254,0,2]` | `[254,0,2]` | export-quantization |
| `(1589,579)` | `[17281,0,16238,65535]` | `[134,0,126,255]` | `[134,0,126]` | `[135,0,127]` | `[135,0,126]` | export-quantization |
| `(898,670)` | `[11280,0,22529,65535]` | `[88,0,175,255]` | `[87,0,175]` | `[88,0,176]` | `[88,0,176]` | export-quantization |

This is a retained Mac-store/formula comparison, not a Windows live field
capture and not AE-exact evidence. It does not justify broad PNG tuning.

## Scope Boundary

- Field words are representative harness inputs, not Windows live field values.
- Local Unicorn addresses are address-formula evidence, not Windows addresses.
- This run is bounded actual-AEX compose evidence, not AE exactness.
- No production source was changed; no broad PNG tuning was performed.

Runner: `tools/emulation/test_olmdistancegradation_pf16_max2_compose_sweep_20260713.py`

Binary SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`

Execution: `12` calls, `1,959` total instructions, per-call cap `200,000`.
