# OLMDistanceGradation PF16 max-2 compose sweep

Date: 2026-07-13

## Result

`PASS`: four bounded calls into the actual 2025 Windows AEX
`FUN_181170480` completed. The runner reused the existing exact-address
witness address/world helpers and made no production or ledger edits.

| Case | XY | Input field word | Field X | Invert | Interp | Render | Power | AEX output AGRB words |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0024 | `(6,40)` | 3989 | 0.1217346191 | 0 | 3 | 1 | 1 | `[32768, 0, 5431, 28661]` |
| 0025 | `(901,394)` | 7774 | 0.2372436523 | 1 | 3 | 1 | 1 | `[32768, 0, 18560, 14896]` |
| 0026 | `(907,222)` | 25680 | 0.7836914062 | 1 | 4 | 1 | 2.5974073410 | `[32768, 0, 9907, 23968]` |
| 0027 | `(1234,443)` | 30473 | 0.9299621582 | 1 | 4 | 2 | 2.5974073410 | `[32768, 0, 32768, 0]` |

Execution total: `653` instructions across `4` calls; per-call cap:
`200000`. All four output buffers were written and all four field-world
`+0x2` words matched the injected values after the call.

## Provenance and limits

- Binary: `aex/OLMDistanceGradation/Plugins/64/2025/DistanceGradation.aex`
- Binary SHA-256: `a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae`
- Runner: `tools/emulation/test_olmdistancegradation_pf16_max2_compose_sweep_20260713.py`
- Existing witness reused: `tools/emulation/olmdg_compose_exact_address_witness_20260710.py`
- Field words are representative harness inputs, not Windows live field values.
  They are based on retained 0026/0027 field-X samples; 0024/0025 are
  representative branch-shape inputs. See the JSON artifact for the explicit
  provenance flag and source references.
- Local Unicorn addresses are address-formula evidence only, not Windows
  address evidence. This run does not claim PF16 store/export equivalence or
  close the 0024..0027 max-2 family.
