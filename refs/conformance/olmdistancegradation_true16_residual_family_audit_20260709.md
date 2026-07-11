# OLMDistanceGradation true16 residual family audit

Date: 2026-07-09

## Decision

The active 16bpc DistanceGradation work is no longer a depthgate-vs-current provenance split. Using the canonical 16bpc PNG reader/verifier, the current installed build has three residual families after the exact slice `0008/0020/0021/0022/0023`.

## Family Summary

| family | cases | family max | nonzero_px sum | classification |
| --- | --- | ---: | ---: | --- |
| `exact` | `0008, 0020, 0021, 0022, 0023` | 0 | 0 | current AE exact slice |
| `sparse_ra_quantization` | `0010, 0011` | 2 | 852 | R and A only, abs delta 2; resembles 16bpc quantization/rounding boundary |
| `layer_no_bg_rounding` | `0012, 0013, 0014, 0016` | 4 | 26957 | mostly abs delta 2; case_0014 has a small abs delta 4 RGB subfamily |
| `field_export_true16` | `0024, 0025, 0026, 0027, 0028` | 3080 | 3721420 | broad true16 residual hidden by byte-view/PIL compare; case_0028 is the outlier max family |

## Case Summary

| case | max | nonzero_px | channel shape | first sample |
| --- | ---: | ---: | --- | --- |
| `0008` | 0 | 0 | exact | `` |
| `0010` | 2 | 351 | R max2 nz351 +344/-7 [2x351]; A max2 nz351 +344/-7 [2x351] | `(6,40) d=[-2, 0, 0, -2]` |
| `0011` | 2 | 501 | R max2 nz501 +501/-0 [2x501]; A max2 nz501 +501/-0 [2x501] | `(915,392) d=[2, 0, 0, 2]` |
| `0012` | 2 | 2948 | R max2 nz2907 +16/-2891 [2x2907]; G max2 nz2596 +0/-2596 [2x2596]; B max2 nz2597 +1/-2596 [2x2597]; A max2 nz155 +24/-131 [2x155] | `(438,0) d=[-2, -2, -2, 0]` |
| `0013` | 2 | 9006 | R max2 nz5811 +1413/-4398 [2x5811]; G max2 nz5308 +1217/-4091 [2x5308]; B max2 nz5308 +1217/-4091 [2x5308]; A max2 nz5394 +5394/-0 [2x5394] | `(15,0) d=[-2, -2, -2, 0]` |
| `0014` | 4 | 9630 | R max4 nz6376 +1536/-4840 [2x6328,4x48]; G max4 nz5765 +1271/-4494 [2x5720,4x45]; B max4 nz5765 +1271/-4494 [2x5720,4x45]; A max2 nz5804 +5804/-0 [2x5804] | `(15,0) d=[-2, -2, -2, 0]` |
| `0016` | 2 | 5373 | R max2 nz5371 +0/-5371 [2x5371]; G max2 nz4988 +0/-4988 [2x4988]; B max2 nz4988 +0/-4988 [2x4988] | `(15,0) d=[-2, -2, -2, 0]` |
| `0020` | 0 | 0 | exact | `` |
| `0021` | 0 | 0 | exact | `` |
| `0022` | 0 | 0 | exact | `` |
| `0023` | 0 | 0 | exact | `` |
| `0024` | 20 | 1051915 | R max20 nz682394 +670849/-11545 [2x648912,4x26077,6x4706]; B max20 nz602191 +580159/-22032 [2x581962,4x15548,8x2576] | `(1,0) d=[2, 0, 0, 0]` |
| `0025` | 6 | 860084 | R max6 nz488757 +458531/-30226 [2x438156,4x35640,6x14961]; B max6 nz599672 +579844/-19828 [2x570817,6x18279,4x10576] | `(3,0) d=[0, 0, 2, 0]` |
| `0026` | 4 | 900709 | R max4 nz530560 +527144/-3416 [2x516349,4x14211]; B max4 nz550389 +533741/-16648 [2x530929,4x17777,1x1683] | `(3,0) d=[0, 0, 4, 0]` |
| `0027` | 4 | 451535 | R max4 nz430193 +426053/-4140 [2x406934,4x23259]; G max4 nz16054 +16044/-10 [2x13891,1x2143,4x20]; B max4 nz20573 +20563/-10 [2x17960,1x2593,4x20] | `(4,0) d=[2, 0, 0, 0]` |
| `0028` | 3080 | 457177 | R max3078 nz437924 +418252/-19672 [2x417487,4x6232,2162x443]; G max3080 nz31998 +15397/-16601 [2x15523,4x2593,6x900]; B max3080 nz36952 +22072/-14880 [2x22966,4x570,6x434] | `(4,0) d=[2, 0, 0, 0]` |

## Next Work

- `0010/0011`: investigate as sparse R/A quantization at the field/export boundary before touching field topology.
- `0012/0013/0014/0016`: keep the current Layer/no-bg improvements; focus on PF16 store/export rounding. `0014` is the only focused Layer case with a small RGB abs-4 subfamily.
- `0024..0028`: rebuild the former near-miss story with true16 arrays. Do not use the old byte-view max=1 classification as implementation proof.

## Verification Source

- Candidate directory: `refs/reports/ae_validation_batch_olmdistancegradation_16bpc_both_rule_20260709/results/bitdepth16_olmdistancegradation_extended_exact`
- Request directory: `handoff/ae_pixel_validation_20260618/requests/ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625`
- PNG reader: `refs/scripts/verify_manifest.py::load_rgba`, matching the canonical verifier.

