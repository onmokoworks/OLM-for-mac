# Windows 32bpc second-generation parity intake

Date: 2026-07-13

## Accepted return

- Return SHA-256:
  `8c1e7df52c4917a9b2872cd52e41a0ad4dac86032d008498499e9d9227d4174f`
- AE `26.3x87`, Software renderer, 32bpc, working space `None`, linear-light
  off, `OLM EXR 32 Float`.
- ColorKey AEX SHA-256:
  `9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c`.
- ToonDilate AEX SHA-256:
  `c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3`.

The dedicated analyzer validates all host/plugin/result fields and hashes.

| Case | Windows effect vs no-effect | Result |
| --- | ---: | --- |
| ColorKey `case_0002` | 0 mismatched FLOAT samples | plugin delta exact |
| ToonDilate `case_0001` | 0 mismatched FLOAT samples | plugin delta exact |

## Cross-host boundary

The exact supplied input EXR changes when AE imports and re-exports it without
an effect: Windows control differs from source in `4,061,236` FLOAT samples
(`max_raw_u32_delta=1019`). Mac and Windows controls then differ in exactly
`6,220,800 = 1920*1080*3` samples, with
`max_raw_u32_delta=36,717,327`; alpha is not in this residual. Windows effect
and control match, and Mac effect and control match, so the same cross-host RGB
residual appears on both effect outputs.

Therefore both plugins are proven no-op exact for these declared cases on each
host, but final Windows-vs-Mac `AE exact` is not proven. The blocker is the
cross-platform EXR import/color interpretation boundary. Do not tune plugin
pixel math from it. Future 32bpc cross-host conformance inputs must either:

1. generate an identical typed float world inside AE on both hosts, or
2. prove and enforce an import interpretation that produces identical
   no-effect controls before comparing effect output.

Machine report:
`refs/conformance/olm_windows_32bpc_second_generation_parity_20260713.json`.

Analyzer:
`scripts/analyze_windows_32bpc_second_generation_return.py`.
