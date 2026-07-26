# OLMSmoother2 no-key 32bpc case-07 Mac AE result

Date: 2026-07-26

## Verdict

`AE exact` is not proven. Windows AE 26.3x87 now has a hash-bound Preserve RGB
recapture using the same FLOAT EXR source contract as Mac. The Windows
same-effect-render PF32 entry is raw exact with the source (`8,294,400/8,294,400`
words, `max_raw_u32_delta=0`), and Windows no-effect vs Mac no-effect is also
raw exact. The attributable effect-on residual is `3,108,911` words with
`max_raw_u32_delta=1,583`.

Reporter status is `candidate_return_verified_effect_mismatch`; Windows
artifact attestation and the PF32 input-entry attestation both pass. The
earlier original-PNG comparison (`2,268,734` mismatches with a very large raw
delta) is superseded as a tuning oracle because its plugin entry was not the
same FLOAT world.

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
- Windows Preserve RGB reference manifest:
  `refs/conformance/olmsmoother2_case07_windows_preserve_rgb_reference_20260727.json`
- Windows AEX SHA-256:
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`
- Windows effect AEP SHA-256:
  `689da9c07512f821c869e0e17031db3d05953896e50b6b2385762f26afcf2f0d`
- `aerender` omitted `-OMtemplate`; the AEP-embedded output settings reported
  `Profile: Preserve RGB (disable color management conversions for this item)`.
  Supplying the Windows-local template was measured to apply a second sRGB
  decode and is rejected by this contract.

The runner compares `Number(pr.gpuAccelType)` with
`Number(GpuAccelType.SOFTWARE)`, accepts only the observed empty/`None`
working-space representations, records the raw value, hashes the bundle
Mach-O rather than the bundle directory, and normalizes AE's single numbered
EXR output fail-closed.

## Artifact identity

| Artifact | SHA-256 |
| --- | --- |
| Bound source FLOAT EXR | `366eb9e01e7c3c60df59dbcf6fb549a57d2156e95105fbea397de5353736c9fb` |
| Windows Preserve RGB no-effect | `046850a4587ef5ca07f120cdd1a990bbac8186accd4f65d7f8f8ec1b0d0d3292` |
| Windows Preserve RGB effect-on (same PF32 witness render) | `404d2b5732adf9bbbc6aadab4a1f0dd075e4e0f911b29076339f6f0e17479cc0` |
| Windows PF32 input entry, uncompressed | `133a9447f8d722a7add9a5c7fc63bcf16b7e77c21cab9aa7c48d84df8677685b` |
| Windows PF32 input entry, gzip artifact | `f29cad40b4f0081fa5f279da0e875198a2970ea2d9c1161db7cc2058acf4044c` |
| Mac no-effect control | `d8fed18b95255511a4622c12e294361cecd2acb1cd93e7e6ebbc87453b7603e3` |
| Mac effect-on | `0231ac0e9a8e960a4e439d0f07ce3f6f017af3b73b300ec21e17eeec61b42d26` |
| Mac return JSON | `81c1d3f0e09e185c141f8b941161a242fdf8dd48a411129f490a3b9174ed1b2f` |

EXR container hashes changed on a second Mac render, but raw semantic FLOAT32
comparison between the two Mac runs was exact for both control and effect
(`mismatched_values=0`, `max_raw_u32_delta=0`). The sample result is
repeatable; container-byte identity is not used as the pixel oracle.

## Raw FLOAT32 gates

| Gate | Mismatched values | Max raw u32 delta | Result |
| --- | ---: | ---: | --- |
| Source FLOAT EXR vs Windows PF32 input entry | 0 | 0 | exact entry gate |
| Windows Preserve RGB no-effect vs Mac no-effect | 0 | 0 | exact output/control gate |
| Windows Preserve RGB effect-on vs repeat Windows effect-on | 0 | 0 | deterministic Windows output |
| Windows Preserve RGB effect-on vs Mac effect-on | 3,108,911 | 1,583 | attributable 32bpc residual |

The PF32 entry was captured at exact AEX RVA `0x4270`, descriptor
`1920x1080`, `rowbytes=30720`, through a read-only CDB +
`ReadProcessMemory` witness. The stored gzip artifact is re-expanded and
compared against the semantic EXR planes by
`scripts/compare_pf32_entry_to_exr.py`; the reporter does not trust a
hand-entered zero-diff claim.

## Next allowed action

Localize and eliminate the now-attributable PF32 effect residual using
binary-grounded 32bpc arithmetic/runtime evidence. Keep the closed 8bpc core
frozen. Re-run the same Preserve RGB entry/no-effect/effect gates after every
32bpc-only change; `AE exact` still requires effect-on `mismatched_values=0`.
