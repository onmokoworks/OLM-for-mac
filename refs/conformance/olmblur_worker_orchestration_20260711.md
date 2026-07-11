# OLMBlur Worker Orchestration Slice

Date: 2026-07-11

## Scope

This artifact covers the 8bpc Non-Legacy worker `FUN_180003710` from the
actual AEX (`f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`).
Its helper calls are the existing exact `FUN_180001000` / `FUN_180001980`
family. It is synthetic worker evidence, not PNG or AE-render evidence.

## Reconstructed orchestration

The worker stages little-endian A,R,G,B bytes into a row-major float RGB plane
and one-byte alpha-validity plane. It allocates two RGB planes and swaps their
roles after each directional pass. Each full directional pass is split into
six helper calls:

| Part | Chunk size | Offset |
| ---: | --- | --- |
| 0..4 | `dimension / 6` | `0, 1q, 2q, 3q, 4q` |
| 5 | `dimension - 5q` | `5q` |

Horizontal calls use row chunks with `FUN_180001000(flags, src, dst,
weights, width, height, chunk_rows, row_offset, radius)`. Vertical calls use
column chunks with `FUN_180001980(flags, src, dst, weights, width, height,
chunk_columns, column_offset, radius)`.

For Bias Direction `1`, each repeat is:

```text
six horizontal calls: plane A -> plane B
six vertical calls:   plane B -> plane A
```

For Bias Direction `2`, the order is reversed. The final output is plane A.

Repeat decay and weights follow the worker instructions:

```text
decay = 1                         if repeat <= 1
decay = powf(3 / blur_amount, 1 / (repeat - 1)) otherwise
radius_d = blur_amount * pow(decay, iteration)
radius = truncate(radius_d)
sigma = float(radius_d) / 3
weight[k] = expf(-(k*k) / ((sigma + sigma) * sigma))
```

The 8bpc writeback stores `floorf(rgb + 0.5f)` to R/G/B and retains the
preinitialized alpha byte, matching the host copy-before-worker setup.

## Exact comparison

Exporter and actual Unicorn worker:
`tools/emulation/test_olmblur_worker_orchestration.py`.

Portable candidate:

- `core/olmblur_worker_orchestration.h`
- `core/olmblur_worker_orchestration.cpp`

Fixture set:
`tools/emulation/fixtures/olmblur_worker_orchestration/`.

Cases include:

- 12x12, radius 3, two repeats, Bias Direction 1;
- 18x18, large radius 11, three repeats, Bias Direction 2.

Replay command:

```text
c++ -std=c++17 -O2 -ffp-contract=off -Icore \
  core/olmblur_helper.cpp core/olmblur_worker_orchestration.cpp \
  tools/emulation/replay_olmblur_worker_orchestration.cpp \
  -o /tmp/replay_olmblur_worker_orchestration
/tmp/replay_olmblur_worker_orchestration \
  tools/emulation/fixtures/olmblur_worker_orchestration
```

Result: `2/2 PASS`, exact byte comparison of complete 8bpc A,R,G,B output
buffers.

The fixture runner installs local `pow` and `powf` import implementations.
The shared loader intentionally leaves those imports generic/unimplemented;
without this bounded test-local registration, the AEX retains stale XMM state
for multi-repeat decay and the large-radius oracle is not valid.

No Mac, ledger, NAS, or PNG/reference files were edited.
