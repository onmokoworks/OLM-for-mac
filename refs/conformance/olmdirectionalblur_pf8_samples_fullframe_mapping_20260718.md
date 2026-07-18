# OLMDirectionalBlur PF8 Samples to Full-Frame Mapping 20260718

- Status: `pass`.
- Scope: Mac-only actual-AEX bounded proof; no AE exact claim and no PNG tuning.
- Production source changed: `False`.

## FACT

- The seven samples from the dated PF8 output contract belong to the natural full `[0,0,16,16]` Iterate8.
- Their coordinates are `(0,0)` through `(6,0)` and map to float cells `(5,5)` through `(5,11)` with `stride_floats=26`.
- Their float byte offsets are computed as `(((row0+y)*stride)+col0+x)*16`; their PF8 destination offsets are `(y*16+x)*4`.
- The actual-AEX padded-world differential passes with `rowbytes=76` and the nonzero `[2,1,14,15]` area; actual and detoured output digests match.
- The source-included Mac adapter probe passes full and partial extent cases with `used_exact=1` and matching PF8 A/R/G/B pixels.

## Evidence

| Check | Result |
| --- | --- |
| `contract_pass` | `True` |
| `actual_aex_writer` | `True` |
| `seven_samples` | `True` |
| `natural_fullframe_iterate` | `True` |
| `sample_cells_map` | `True` |
| `sample_bytes_map` | `True` |
| `sample_row_contiguous` | `True` |
| `actual_aex_padded_world` | `True` |
| `mac_writer_adapter` | `True` |
| `fail_closed` | `True` |

## Boundary

- This connects the seven actual-AEX writer samples to coordinate and row/stride contracts. It is not a same-run complete-frame capture.
- `AE exact` remains `False`; broad full-frame comparison and PNG tuning remain out of scope.

## Reproduction

`python3 tools/emulation/test_olmdirectionalblur_pf8_samples_fullframe_mapping_20260718.py`
