# OLMRadialBlur Scatter-Tail Equivalence

- Status: `pass`
- Target: `0x180001c90` in `aex/OLMRadialBlur/Plugins/64/2025/OLMRadialBlur.aex`
- Pinned AEX SHA-256: `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- Execution: Mac-local Unicorn only; no AE, Windows, PNG, or production edits.
- C++ portable core probe: `pass`.
- C++ UBSan replay: `pass`.

## Contract

- Mode 1 adds caller distance; mode 2 takes max; mode 3 uses caller distance; resolved span is upper-clamped at 3000.
- Effective length uses `CVTTSS2SI r32`: truncate finite in-range float32 toward zero, and return `INT32_MIN` for NaN or out-of-range input. The helper exits for that non-positive sentinel.
- Samples use offsets `1 <= offset < effective_len`, with outer table `ctx+0x68` and inner table `ctx+0x1d528`.
- Outer wraps within the current radius row. Inner underflow advances to the next radius row tail.
- The source-NaN claim is limited to AEX-proven payload `0x7fc12345`; it propagates unchanged to two RGBA destinations while seeded max-alpha values remain unchanged. Span-gate payload `0x7fc54321` and the overflowing finite fixture both produce the captured `INT32_MIN` sentinel and no writes.
- The contract assumes valid 30,000-entry tables, `angular_count=4`, and buffers covering every reached fixture cell. The portable `cell >= cell_count` early return is an intentional safety divergence; the AEX has no equivalent check, and undersized-buffer behavior is not claimed.

## Fixtures

| Fixture | Effective len AEX/ref | Exact buffers | Instructions |
| --- | --- | --- | ---: |
| `mode1_span_adds_caller_distance` | `5/5` | `True` | 221 |
| `mode2_span_uses_max` | `4/4` | `True` | 185 |
| `resolved_span_clamps_to_3000` | `6/6` | `True` | 262 |
| `effective_len_float32_truncation` | `3/3` | `True` | 150 |
| `outer_table_sample_origin_is_one` | `3/3` | `True` | 150 |
| `inner_table_base_and_row_tail_underflow` | `3/3` | `True` | 156 |
| `persistent_max_alpha_is_not_overwritten_by_lower_tap` | `3/3` | `True` | 149 |
| `nan_source_payload_propagates_and_max_stays` | `3/3` | `True` | 148 |
| `span_gate_nan_cvtt_sentinel_no_write` | `-2147483648/-2147483648` | `True` | 43 |
| `span_gate_out_of_range_cvtt_sentinel_no_write` | `-2147483648/-2147483648` | `True` | 43 |

## Reproduction

```text
python3 tools/emulation/test_radialblur_scatter_tail_equivalence_20260717.py
```

## Interpretation

A `pass` is a function-level equivalence result for the pinned AEX contract, not an AE-host or rendered-image claim. Any hash mismatch or byte mismatch fails closed and blocks production implementation decisions.

The release and UBSan C++ probes use `-fno-fast-math -ffp-contract=off` and consume the ten recorded AEX output buffers from this report through a temporary binary fixture vector.
