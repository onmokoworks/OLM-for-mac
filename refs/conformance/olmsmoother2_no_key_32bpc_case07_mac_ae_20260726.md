# OLMSmoother2 no-key 32bpc case-07 Mac AE result

Date: 2026-07-26

## Verdict

`AE exact` is not proven. The same-contract no-effect control differs before
the effect can be attributed, and the retained Windows manifest does not bind
the per-artifact hashes and header metadata required by the request.

The covered 8bpc implementation remains frozen and exact. This result does not
authorize any 8bpc core change.

## Bound contract

- Request:
  `refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json`
- Case: `final_random10_olm_smoother_v2_07`
- Case-contract SHA-256:
  `9ac98538107d520686870917718882d2ae593a94032f071a34430cf222e3f8af`
- macOS: `15.7.2` build `24G325`
- After Effects: `26.3x87`
- Project: `32bpc`, `SOFTWARE`, working space raw `None`, linear blending
  `false`, `1920x1080`, `24 fps`
- Loaded Mach-O SHA-256:
  `d7abbd9dc16cc168f2c8ee8178d262f6fd8fceb618febf906e301e405b957d18`
- Output: uncompressed scanline OpenEXR, physical channels `A,B,G,R`, all
  sample type `FLOAT`, `8,294,400` finite samples per file, no NaN or Inf

The runner compares `Number(pr.gpuAccelType)` with
`Number(GpuAccelType.SOFTWARE)`, accepts only the observed empty/`None`
working-space representations, records the raw value, hashes the bundle
Mach-O rather than the bundle directory, and normalizes AE's single numbered
EXR output fail-closed.

## Artifact identity

| Artifact | SHA-256 |
| --- | --- |
| Windows before-effects | `366eb9e01e7c3c60df59dbcf6fb549a57d2156e95105fbea397de5353736c9fb` |
| Windows effect-on | `95f0339e428e85803b3f6c806632938827b70574a88392abd3ab9c1af22af1c5` |
| Mac no-effect control | `c3f1b49307adffe5a68270893fd02a42b84ecb7d168b8b91ecaded89a3e185d7` |
| Mac effect-on | `c68c38aed1ab7f7b8183f4071f81c8f0cf7fa59e2a05ed38a6859e57f5e145d2` |
| Mac return JSON | `9348ee733ae72a9b251c5f77096f159a1ca90b3b8555112f3463933657424947` |
| Validation report | `cc1e19683c45bd68f494956ba1b7e7f2fb05ef0a00184645db087be692b819bc` |

EXR container hashes changed on a second Mac render, but raw semantic FLOAT32
comparison between the two Mac runs was exact for both control and effect
(`mismatched_values=0`, `max_raw_u32_delta=0`). The sample result is
repeatable; container-byte identity is not used as the pixel oracle.

## Raw FLOAT32 gates

| Gate | Mismatched values | Max raw u32 delta | Result |
| --- | ---: | ---: | --- |
| Windows before-effects vs Mac no-effect | 6,106,918 | 94,228,095 | fail |
| Windows effect-on vs Mac effect-on | 6,108,445 | 94,228,099 | fail, not attributable |

The control failure is evaluated first. Therefore the effect-on mismatch is a
cross-host result under an already-red host/export path, not evidence that the
Mac smoothing algorithm is wrong.

## Next allowed action

Obtain an aligned Windows/Mac no-effect capture whose project color state,
source interpretation, output-module settings, artifact attestation, and raw
FLOAT32 words all match. Only after that control passes may the effect-on
residual be attributed. Do not tune the closed 8bpc core from this 32bpc
result.
