# OLMDirectionalBlur Row 755 Return: Binding Success, Artifacts Missing

Date: 2026-07-12

## Classification

`exact_bind_failure`. This return is not an answered typed witness and cannot
be promoted to algorithm evidence.

## FACT

- The Windows AEX size and SHA-256 matched the requested binary exactly:
  `56832` bytes,
  `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- The same-run AE pause/continue handshake completed.
- The debugger emitted `DBR_STAGE`, `DBR_PROVENANCE`, and
  `DBR_CAPTURE_END` at normalization offset `0x5554`.
- The live provenance was:
  - `rowdriver_calls=32`
  - `row_start=0`, `row_end=2176`
  - `row0=563`, `col0=143`, `stride=2206`
  - destination, denominator, and alpha-valid plane pointers from the same
    params pointer.
- The three required artifacts were absent from the returned run:
  `row755_destination_rgba_f32_le.bin`,
  `row755_denominator_f32_le.bin`, and
  `row755_alpha_valid_f32_le.bin`.
- CDB reported partial write counts (`4678`, `0xcd0`, `0xcd0`) rather than
  the required `5344`, `1336`, and `1336` bytes.

## INFERENCE

- The origin-aware address/provenance contract is now exercised successfully;
  the remaining failure is artifact capture/serialization or an unreadable
  portion of the requested range, not module binding.
- The next retry should capture bounded chunks and return a work-directory
  listing plus each chunk size. A partial row must remain rejected.

## Intake

The return was verified with `scripts/verify_runtime_trace_return.py` and
archived under `/Volumes/onmk/olm_pr/old/`. No production source changed.
