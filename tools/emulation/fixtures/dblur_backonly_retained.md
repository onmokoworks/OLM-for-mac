# DirectionalBlur retained Back-only regression bytes

`dblur_backonly_retained.argb` contains 28,672 active output bytes from the
pre-F01 retained native implementation at
`db59044515791af9890d0768c1fa4c7f5ad34034`, not a new AEX reference.
SHA-256: `8722e9bfd894895b9148dda941ada8bfb08b119a0e3e80ac42e17c8f1d8600c6`.

The original `retained_depth` probe supplies deterministic 16×16 inputs with
5 input-padding and 17 output-padding bytes per row, front=0, scale=1,
noise type=1, seed=1, thickness=10. The capture requires the original retained
route, successful render, changed output, unchanged input and intact padding.
Only active ARGB bytes are stored, in row order, using native little-endian
PF8/PF16/PF32 channel representation:

| Offset | Depth | (back, angle, gain), in order |
| ---: | ---: | --- |
| 0 | 8 | (8, 0, 1), (8, 45, 1) |
| 2048 | 16 | (1, 45, 1), (2, 45, 1), (8, 45, 1) |
| 8192 | 32 | (1, 0, 0.5), (1, 0, 1), (1, 45, 0.5), (1, 45, 1), (8, 45, 1) |

Reproduce from the repository root (requires the normal AE SDK links):

```sh
mkdir -p orchestra/state/G01-gate-after-cleanup/tmp
TMPDIR="$PWD/orchestra/state/G01-gate-after-cleanup/tmp" \
python3 -B orchestra/reports/G01-evidence/capture_retained.py \
  > orchestra/state/G01-gate-after-cleanup/capture.log 2>&1
cmp tools/emulation/fixtures/dblur_backonly_retained.argb \
  orchestra/state/G01-gate-after-cleanup/capture/retained.argb
```

The current probe checks bytes independently of dispatch route and reports the
first mismatch with depth, case parameters, active-byte offset and both values.
