# OLMSmoother2 observed writer-frame replay

## Verdict

`PARTIAL_SMOOTHER2_OBSERVED_WRITER_FRAME_REPLAY`

Observed Windows writer-frame float4 tuples were fed directly into the checked-in AEX PF8 typed worker. The result is fail-closed: one tuple reproduces and one does not.

## Results

| Case | Windows writer-frame RGBA float4 | Windows PF8 ARGB integer | Windows memory bytes | AEX memory bytes | Result |
| --- | --- | --- | --- | --- | --- |
| `legacy_case_0004_writer_frame` | `[0.80824906, 0.80824906, 0.80824906, 0.44156867]` | `e8e8e871` | `71e8e8e8` | `71cecece` | `not_reproduced_from_supplied_float_tuple` |
| `legacy_case_0012_writer_frame` | `[1.0, 1.0, 1.0, 0.0]` | `ffffff00` | `00ffffff` | `00ffffff` | `reproduced` |

## FACT

- The AEX PF8 worker consumed both supplied float4 tuples and produced deterministic raw bytes.
- Case 0012 reproduces the Windows packed record after interpreting the logged integer as little-endian memory bytes.
- Case 0004 does not: the supplied tuple produces `71cecece`, while the Windows packed record is `71e8e8e8` in memory order.
- The worker and AEX identity are checked by the existing typed-writeback grounding.

## INFERENCE

- The writer is not ruled out: the 0004 tuple may not be the actual writer-entry tuple, or the Windows raw record may refer to another stage/packing convention.
- The 0012 match alone is insufficient to generalize the writer boundary.
- This does not identify the upstream config, crop translation, classifier, c280, or cce0 state; no production behavior was changed.

## Reproduction

```sh
python3 tools/emulation/audit_olmsmoother2_writer_frame_replay_20260718.py
```
