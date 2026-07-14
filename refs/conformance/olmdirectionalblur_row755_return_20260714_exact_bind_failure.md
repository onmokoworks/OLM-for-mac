# OLMDirectionalBlur row 755 return: typed provenance bound, capture contract corrected

Date: 2026-07-14

Return archive:

`refs/windows_returns/20260714/20260714_1700__RETURN__OLMDIRECTIONALBLUR_ROW755__single_fixed.zip`

## Classification

`exact_bind_failure`. This is not an answered typed witness and is not an
`AE exact` result.

## FACT

- The requested AEX hash matched: `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- The run used AE `25.2x131`, Software renderer, and 8bpc.
- The same run bound `DBR_WORKER_ENTRY` once and `DBR_ROW_RANGE` 32 times.
- The rowdriver ranges covered `0..2176`; row 755 was covered and
  `params_mismatch=0`.
- The captured params reported `row0=563`, `col0=143`, `stride=2206`,
  `row=755`, `x_start=747`, and `x_end=1080`.
- The return failed because the contract required `row_end=2206`, while the
  observed value was `row_end=2176`.
- No pre-normalization plane artifacts were accepted from this return.

## Decision

The witness contract now distinguishes the observed row extent (`2176`) from
the row stride (`2206`). The CDB address calculation continues to use the
stride field. This correction is evidence-bound and does not change the Mac
algorithm.

## Next evidence required

Re-run the same focused package after the contract correction. Acceptance
requires the three typed pre-normalization plane artifacts, their declared
byte sizes (`5344`, `1336`, `1336`), and a successful validator status.

