# OLMSmoother2 post-cce0 typed writeback boundary

## Verdict

`PASS_ACTUAL_AEX_POST_CCE0_TYPED_WRITEBACK_ORACLE`

The checked-in AEX executes each depth-specific worker through its explicit nine-argument ABI and serial dynamic-VCOMP callback. The corresponding wrappers are statically grounded. A zero class plane makes c280 select the center sample; the independent oracle checks only the subsequent typed store.

## Results

| Depth | Wrapper | Worker | Raw output | Equal |
| --- | --- | --- | --- | --- |
| `PF8` | `0x180003d00` | `0x180003370` | `9f1f80e0` | `True` |
| `PF16` | `0x180003e20` | `0x180003990` | `0050cd0f00403370` | `True` |
| `PF32` | `0x180003d90` | `0x1800036e0` | `0000203fded6fc3d0000003f2365603f` | `True` |

The oracle uses float32 source values, A,R,G,B byte/word order, and the independently transcribed `+0.5` truncating quantization with scales `255` and `32768`; PF32 is compared as raw float32 words.

## Boundary

This closes only the bounded post-cce0 typed writeback workers for a center-sample fixture. It does not claim classifier, c280, cce0 algorithm, Windows behavior, host state, or AE exactness.

## Reproduction

```sh
python3 tools/emulation/test_olmsmoother2_typed_writeback_20260717.py --output-json refs/conformance/olmsmoother2_typed_writeback_20260717.json --output-md refs/conformance/olmsmoother2_typed_writeback_20260717.md
```
