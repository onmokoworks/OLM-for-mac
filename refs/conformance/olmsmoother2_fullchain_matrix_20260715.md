# OLMSmoother2 Local c280-to-cce0 Matrix

Date: 2026-07-15

## Verdict

`PASS_SUPPORTED_LOCAL_BINARY_DIFFERENTIAL_WITH_DISPATCH_GAP`

This is local binary-semantic and local emulation evidence only. It is not
Windows AE truth, AE exact evidence, or a claim that the synthetic fixtures
are the live case_0012 memory state.

## Commands

```sh
python3 refs/scripts/smoke_smoother2_fullchain_diff.py
python3 tools/emulation/test_smoother2_producer.py
python3 tools/emulation/test_smoother2_typed_witness.py --output-json /tmp/olmsmoother2_typed_20260715.json --output-md /tmp/olmsmoother2_typed_20260715.md
python3 tools/emulation/test_smoother2_case0012_local_tuple.py --output /tmp/olmsmoother2_tuple_20260715.json
```

The fullchain smoke compiled the C++ adapter with `clang++ -std=c++17 -O2`
and ran the checked-in 2025 AEX through `AexLoader`.

## Supported Matrix

| Fixture | classifier | e170 c | producer | c280 count | cce0 / accumulation |
| --- | ---: | ---: | --- | ---: | --- |
| `c2_witness` | `0x69` | `2` | append | `1` | PASS |
| `c4_control` | `0x69` | `4` | f270 suppress | `0` | PASS |
| `classifier_zero` | `0xff` | `2` | direct producer append | `0` | PASS empty-builder path |

For all three rows, actual AEX and portable adapter comparisons passed for
classifier output, descriptor/cardinal dispatch, producer vertices and
weights, normalization, c280 entry versus portable builder, cce0 entry versus
portable orchestrator in both no-gamma and Gamma Colors fixtures, and the
independent clamped-weight cce0 accumulation replay at `1e-6`.

The producer sweep also covers all eight combinations of the three e170 input
bits and scanner spans `{0,1,2,3,6}` with both values of the left-neighbor
guard byte. The typed witness confirms `c=2 -> f270 append` and `c=4 -> f270
suppress`, while direct e3a0 remains appendable in the control row.

## Gap

A preliminary all-one classifier neighborhood produced AEX classifier `0x40`
and two c280 samples, while the current portable dispatch produced two samples
with different weights and cce0 floats. That branch is excluded from the pass
gate and remains an adapter/port dispatch gap. No source change was made to
force it to match.

The actual AEX c280/cce0 tuple replay from the grounded 5x5 case_0012 log also
passed as local execution, but its translated origin is not promoted to a
Windows host binding or AE result.

## Claim Boundary

No Windows class/config binding, AE host packing, final render truth, or
production-plugin exactness is established. `notes/CONFORMANCE_LEDGER.md` was
not edited.
