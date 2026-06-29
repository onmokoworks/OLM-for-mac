# OLMDistanceGradation 16bpc Power-Fix Residual Families (2026-06-29)

- Source report: `refs/reports/ae_pixel_validation_16bpc_distancegradation_extended_powerfix_20260629_1424/reports/ae_pixel_16bpc_extended_powerfix.json`
- Exact: `1/16`

## Families

| Family | Count |
| --- | ---: |
| `ae-exact` | 1 |
| `both-no-bg-zero-threshold-edge-case` | 1 |
| `constant-bg-binary-sparse-full-color` | 4 |
| `layer-no-bg-source-or-alpha-ownership` | 4 |
| `power-layer-bg-source-or-premultiply` | 2 |
| `power-rgb-bg-boundary-quantization` | 1 |
| `sparse-boundary-quantization` | 1 |
| `sphere-bg-boundary-quantization` | 2 |

## Cases

| Case | Family | max | mean | nonzero_px | Params | First max witness |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `olmdistancegradation_extended__case_0008` | `ae-exact` | 0 | 0.0000 | 0 | `inv=0 inout=2 in=369 out=0 mode=1 bg=0 interp=2 power=1` | `(0,0) ch0 ref=[0, 0, 0, 0] cand=[0, 0, 0, 0] delta=[0, 0, 0, 0]` |
| `olmdistancegradation_extended__case_0010` | `sparse-boundary-quantization` | 1440 | 1.2139 | 11228 | `inv=0 inout=3 in=63 out=82 mode=1 bg=0 interp=2 power=1` | `(987,26) ch0 ref=[61217, 0, 0, 61217] cand=[62657, 0, 0, 62657] delta=[1440, 0, 0, 1440]` |
| `olmdistancegradation_extended__case_0011` | `both-no-bg-zero-threshold-edge-case` | 65347 | 1.0476 | 4290 | `inv=0 inout=3 in=348 out=0 mode=1 bg=0 interp=2 power=1` | `(1699,7) ch0 ref=[0, 0, 0, 0] cand=[65347, 0, 0, 65347] delta=[65347, 0, 0, 65347]` |
| `olmdistancegradation_extended__case_0012` | `layer-no-bg-source-or-alpha-ownership` | 16250 | 53.4510 | 25421 | `inv=0 inout=3 in=122 out=204 mode=2 bg=0 interp=2 power=1` | `(462,7) ch0 ref=[32371, 32371, 32371, 64997] cand=[16121, 16121, 16121, 64997] delta=[-16250, -16250, -16250, 0]` |
| `olmdistancegradation_extended__case_0013` | `layer-no-bg-source-or-alpha-ownership` | 9658 | 26.2368 | 17273 | `inv=0 inout=1 in=53 out=204 mode=2 bg=0 interp=2 power=1` | `(101,347) ch0 ref=[30627, 30627, 30627, 44377] cand=[20969, 20969, 20969, 44025] delta=[-9658, -9658, -9658, -352]` |
| `olmdistancegradation_extended__case_0014` | `layer-no-bg-source-or-alpha-ownership` | 9686 | 26.5946 | 18275 | `inv=0 inout=1 in=424 out=204 mode=2 bg=0 interp=2 power=1` | `(1652,2) ch0 ref=[29399, 29399, 29399, 43843] cand=[19713, 19713, 19713, 43843] delta=[-9686, -9686, -9686, 0]` |
| `olmdistancegradation_extended__case_0016` | `layer-no-bg-source-or-alpha-ownership` | 9710 | 26.6457 | 14196 | `inv=1 inout=1 in=0 out=204 mode=2 bg=0 interp=2 power=1` | `(106,19) ch0 ref=[29125, 29125, 29125, 43689] cand=[19415, 19415, 19415, 43689] delta=[-9710, -9710, -9710, 0]` |
| `olmdistancegradation_extended__case_0020` | `constant-bg-binary-sparse-full-color` | 61165 | 14.4223 | 1001 | `inv=0 inout=1 in=78 out=204 mode=1 bg=1 interp=1 power=1` | `(951,417) ch2 ref=[7195, 0, 61165, 65535] cand=[65535, 0, 0, 65535] delta=[58340, 0, -61165, 0]` |
| `olmdistancegradation_extended__case_0021` | `constant-bg-binary-sparse-full-color` | 61165 | 14.4367 | 1002 | `inv=0 inout=3 in=78 out=402 mode=1 bg=1 interp=1 power=1` | `(1919,388) ch2 ref=[7195, 0, 61165, 65535] cand=[65535, 0, 0, 65535] delta=[58340, 0, -61165, 0]` |
| `olmdistancegradation_extended__case_0022` | `constant-bg-binary-sparse-full-color` | 61165 | 134.6708 | 9347 | `inv=0 inout=3 in=36 out=11 mode=1 bg=1 interp=1 power=1` | `(4,0) ch2 ref=[7195, 0, 61165, 65535] cand=[65535, 0, 0, 65535] delta=[58340, 0, -61165, 0]` |
| `olmdistancegradation_extended__case_0023` | `constant-bg-binary-sparse-full-color` | 61165 | 19.9982 | 1388 | `inv=0 inout=3 in=36 out=0 mode=1 bg=1 interp=1 power=1` | `(1699,7) ch2 ref=[65535, 0, 0, 65535] cand=[7195, 0, 61165, 65535] delta=[-58340, 0, 61165, 0]` |
| `olmdistancegradation_extended__case_0024` | `sphere-bg-boundary-quantization` | 20669 | 2.4806 | 1054204 | `inv=0 inout=3 in=158 out=17 mode=1 bg=1 interp=3 power=1` | `(320,183) ch2 ref=[65535, 0, 0, 65535] cand=[45821, 0, 20669, 65535] delta=[-19714, 0, 20669, 0]` |
| `olmdistancegradation_extended__case_0025` | `sphere-bg-boundary-quantization` | 16656 | 1.9855 | 862157 | `inv=1 inout=3 in=158 out=13 mode=1 bg=1 interp=3 power=1` | `(1699,7) ch2 ref=[43093, 0, 23525, 65535] cand=[58981, 0, 6869, 65535] delta=[15888, 0, -16656, 0]` |
| `olmdistancegradation_extended__case_0026` | `power-rgb-bg-boundary-quantization` | 11480 | 2.9254 | 902747 | `inv=1 inout=3 in=158 out=13 mode=1 bg=1 interp=4 power=2.59740734100342` | `(876,130) ch2 ref=[7195, 0, 61165, 65535] cand=[18147, 0, 49685, 65535] delta=[10952, 0, -11480, 0]` |
| `olmdistancegradation_extended__case_0027` | `power-layer-bg-source-or-premultiply` | 12301 | 1.5706 | 454039 | `inv=1 inout=3 in=158 out=13 mode=2 bg=1 interp=4 power=2.59740734100342` | `(876,130) ch0 ref=[0, 0, 0, 65535] cand=[12301, 0, 0, 65535] delta=[12301, 0, 0, 0]` |
| `olmdistancegradation_extended__case_0028` | `power-layer-bg-source-or-premultiply` | 14750 | 8.1905 | 459649 | `inv=1 inout=3 in=158 out=13 mode=2 bg=1 interp=4 power=0.40016460418701` | `(1699,7) ch0 ref=[42143, 91, 91, 65535] cand=[56893, 0, 0, 65535] delta=[14750, -91, -91, 0]` |

## Reading

- The Power parameter collapse is fixed and should not be revisited.
- Remaining work should be split by family rather than tuned from all failures together.
- `constant-bg-binary-sparse-full-color` is still a full-color branch mismatch on sparse pixels.
- `power-layer-bg-source-or-premultiply` needs source/premultiply ownership evidence.
- `power-rgb-bg-boundary-quantization` and `sphere-bg-boundary-quantization` need final field quantization / writeback proof.
