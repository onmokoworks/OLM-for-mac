# OLMDistanceGradation PF16 store boundary audit

- Date: 2026-07-18
- Status: `pass` for the bounded actual-AEX experiment; `AE exact` is not claimed.
- Scope: checked-in Windows 2025 AEX `FUN_181170480`, called under Mac-local Unicorn.
- Production source changed: **no**.

## FACT

- The experiment injects field words and gradient values that place the red pre-store value around PF16 half-code boundaries.
- The AEX output word order is `A,G,R,B`; the red word is the third word in the returned tuple.
- The actual AEX red word matches the truncation model for every bounded witness.
- The same rows do not uniformly match half-up or nearest-even.

| witness | field | grad R | pre-store R | AEX R | trunc | half-up | even |
|---|---:|---:|---:|---:|---:|---:|---:|
| `half_code_at_zero_field` | 0 | 1.525878906e-05 | 1.525878906e-05 | 0 | 0 | 1 | 0 |
| `odd_half_code_at_zero_field` | 0 | 4.577636719e-05 | 4.577636719e-05 | 1 | 1 | 2 | 2 |
| `even_half_code_at_zero_field` | 0 | 7.629394531e-05 | 7.629394531e-05 | 2 | 2 | 3 | 2 |
| `half_code_after_field_step` | 1 | 4.577636719e-05 | 7.629254833e-05 | 2 | 2 | 2 | 2 |
| `midfield_half_code` | 16384 | 9.155273438e-05 | 0.5000457764 | 16385 | 16385 | 16386 | 16386 |
| `near_zero_after_inversion` | 32767 | 1.5 | 1.000015259 | 32768 | 32768 | 32768 | 32768 |

## INFERENCE

This local result does not prove that the 0012/0014 RGB residual is upstream. It does prove that a global replacement of the current truncation-shaped compose/store rule with half-up or nearest-even is not justified by the actual AEX boundary. The required next witness is one same-run Windows and Mac coordinate from each target case carrying both pre-store float and final PF16 word.

## Reproduction

```sh
python3 tools/emulation/audit_olmdistancegradation_pf16_store_boundary_20260718.py
python3 tools/emulation/test_olmdistancegradation_pf16_store_boundary_20260718.py
```

## Evidence

- `refs/conformance/olmdistancegradation_16bpc_nearmiss_boundary_20260718.md`
- `refs/conformance/olmdistancegradation_pf16_boundary_matrix_20260717.json`
- `refs/conformance/olmdistancegradation_pf16_field_staging_exact_20260717.json`
- `refs/conformance/olmdistancegradation_depth_gate_result_20260708.md`
