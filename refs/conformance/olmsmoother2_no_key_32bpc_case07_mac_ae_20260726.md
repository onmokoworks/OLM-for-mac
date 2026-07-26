# OLMSmoother2 no-key 32bpc case-07 Mac AE result

Date: 2026-07-26

## Verdict

`AE exact` is not proven. The Preserve-RGB no-effect output gate is raw
FLOAT32 exact, but plugin-input equivalence is not: the retained Windows
effect reference starts from the original PNG import, while this Mac effect
run re-imports the Windows before-effects EXR through a hash-bound Preserve
RGB AEP template. No same-run Windows PF32 input-entry witness proves that the
two effect invocations receive identical float worlds. The retained Windows
manifest also does not bind the per-artifact hashes and header metadata
required by the request.

The covered 8bpc implementation remains frozen and exact. This result does not
authorize any 8bpc core change.

## Bound contract

- Request:
  `refs/mac_validation_requests/olmsmoother2_no_key_32bpc_mac_validation_20260715.json`
- Case: `final_random10_olm_smoother_v2_07`
- Case-contract SHA-256:
  `e8870b11b7a072b84fe8e4554c9e058468f15f7daf5b4be0d576d6b00a980403`
- macOS: `15.7.2` build `24G325`
- After Effects: `26.3x87`
- Project: `32bpc`, `SOFTWARE`, working space raw `None`, linear blending
  `false`, `1920x1080`, `24 fps`
- Loaded Mach-O SHA-256:
  `d7abbd9dc16cc168f2c8ee8178d262f6fd8fceb618febf906e301e405b957d18`
- Input interpretation: hash-bound
  `refs/fixtures/olmsmoother2_32bpc_preserve_rgb_input_template_20260726.aep`,
  SHA-256
  `51fd5403b0a43825f0f6d189c49154ad756f4c565498f733c1fb725377583679`;
  `FootageItem.replace()` preserves RGB for the Windows before-effects FLOAT
  EXR and rejects template/effect contamination
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
| Mac no-effect control | `d8fed18b95255511a4622c12e294361cecd2acb1cd93e7e6ebbc87453b7603e3` |
| Mac effect-on | `0231ac0e9a8e960a4e439d0f07ce3f6f017af3b73b300ec21e17eeec61b42d26` |
| Mac return JSON | `81c1d3f0e09e185c141f8b941161a242fdf8dd48a411129f490a3b9174ed1b2f` |
| Validation report | `582ac600094725b366937c630fa301e46ff689e6fd50b511c5fab3a9374c9529` |

EXR container hashes changed on a second Mac render, but raw semantic FLOAT32
comparison between the two Mac runs was exact for both control and effect
(`mismatched_values=0`, `max_raw_u32_delta=0`). The sample result is
repeatable; container-byte identity is not used as the pixel oracle.

## Raw FLOAT32 gates

| Gate | Mismatched values | Max raw u32 delta | Result |
| --- | ---: | ---: | --- |
| Windows before-effects vs Mac no-effect | 0 | 0 | exact output/control gate |
| Windows effect-on vs Mac effect-on | 2,268,734 | 991,472,415 | fail |

The exact no-effect gate proves the Preserve-RGB Mac import/export path can
round-trip the retained Windows before-effects EXR. It does not prove that the
Windows original-PNG effect run and the Mac Preserve-RGB EXR effect run enter
OLMSmoother2 with identical `PF_PixelFloat` words. The effect residual is
therefore measured but is not yet safe as a tuning oracle.

Reporter status is `blocked_input_entry_identity`; both
`windows_pf32_input_entry_attestation_present` and admissible Windows artifact
attestation are false.

## Next allowed action

Capture the Windows PF32 input entry in the original-PNG case-07 run, or
recapture Windows from the identical Preserve-RGB FLOAT EXR source contract.
Bind that witness and both Windows artifacts to same-run hashes/header
metadata, then compare effect-on raw FLOAT32 words. Do not tune the closed
8bpc core from the current residual.
