# AEXCompat OLM Execution Pilot (2026-07-25)

## Scope

This pilot checks whether AEXCompat can execute an unchanged Windows OLM AEX
locally on Apple Silicon and produce evidence useful for the OLM port. It does
not promote any Mac plug-in lane to `AE exact`.

## Provenance

- AEXCompat integrated commits: `1fe322b`, `ae5cbcc`, `59e002c`,
  and `3adba76`
  (`codex/olm-suite-followup`)
- `aex-guest-worker` SHA-256:
  `4d0018c95cb26dc32261c56969566db7deeace9b6c39c6daaa3f9773adbc214f`
- post-expansion `aex-guest-worker` SHA-256:
  `bc4cb0d6aa38b67a3e6d0f7df1c252724f8ac720a15b346b48e291940338c6db`
- OLMRadialBlur 2025 AEX SHA-256:
  `ffbb1d0109671e3ea9b1a12cd1126f2c72f965197577a57cc602fb096414ccdb`
- OLMSmoother2 2025 AEX SHA-256:
  `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`
- Windows AEX: OLMBlur 2025
- Windows AEX SHA-256:
  `f0611785e7b14ac4fcfc75f23b8862beb4539eee52d25d472556849535e96e5b`
- Reference request: normalized OLMBlur Windows Software 8bpc package
- Input `case_0001` SHA-256:
  `cc1bf1aa128dea6197405ee722c66198fb5fcbc213bf2569c7af9f30be4fa4f4`
- Reference `case_0001` PNG SHA-256:
  `1635b7daf8c08d94c3316aee1d53534a5d04adacb859d9f7bc9e5caa4569bf75`

## Full-frame calibration

The unchanged Windows AEX was executed through AEXCompat `render-png` at
960x540 with the parameters taken directly from `reference_manifest.json`.

| Case | Result | max diff | differing pixels |
| --- | --- | ---: | ---: |
| `case_0001` | pixel exact | 0 | 0 / 518400 |
| `case_0002` | pixel exact | 0 | 0 / 518400 |
| `case_0003` | execution budget exhausted | n/a | n/a |

PNG file hashes differ because the encoders write different container bytes.
Decoded RGBA pixels for `case_0001` and `case_0002` are identical.
The integrated `1fe322b` worker was re-run after the suite additions and
remained decoded-pixel exact against the packaged normalized Software
candidates for both cases. The older `refs/win_references/20260604_olm`
flat PNGs differ by `max=59` and are not the normalized Software oracle used
for this calibration.

`case_0003` is a heavy Legacy case (`Amount=248.6`, `Repeat=10`). The worker
stopped at RVA `0x16d6` before returning. This is an AEXCompat execution-budget
limit, not a pixel mismatch.

## Dossier calibration

A 32x32 resized probe was used only to validate trace semantics. It is not a
conformance image. Both `Amount=5` and `Amount=10` completed with
`render_error=0`, and every selector had an empty `truncation` array.

Changing only Amount produced the following bounded facts in `SMART_RENDER`:

- direct call site RVA `0x3710`
- return site RVA `0x3e33`
- target/import thunk RVA `0xccae`
- imported operation: `expf`
- observed calls: `10 -> 15`
- Amount appears as `xmm1.f64[0]`: `5.0 -> 10.0`
- Amount divided by three appears as `xmm2.f32[0]`:
  `1.6666666269302368 -> 3.3333332538604736`

The `expf` input sequence also changes consistently with Amount. This proves
that the dossier can connect an AE-visible parameter to a concrete AEX kernel
call path and its Win64 floating-point arguments.

## Host-suite expansion

The following guest host boundaries were added and independently reviewed:

- AEGP Memory Suite v1 slots 0 through 5, with failure-state atomicity
- PF World Suite v2 slots 0 through 2 for ARGB8, ARGB16, and ARGB32F worlds
- PF PointParamSuite v1 current-value conversion from signed 16.16 to doubles
- point default materialization from percentage defaults to source coordinates
- `Name@slot=value` parameter selection for duplicate AE-visible names
- scalar, angle, and two-dimensional point CLI assignments
- PF Handle allocations in a separate 64-bit address range, including the
  observed 333,294,848-byte RadialBlur request
- deterministic `vcomp140.dll!omp_get_max_threads` emulation returning one
- strict slot-qualified ARGB8 color transport and PF ColorParamSuite v1 in
  Unicorn and the native carrier

The integrated worker completed local 32x32 Smart Render calls for the
unchanged 2025 `OLMSmoother2.aex` and `OLMRadialBlur.aex` with
`render_error=0`. Smoother2 requested both AEGP Memory Suite v1 and PF World
Suite v2. RadialBlur requested PF PointParamSuite v1. These are host-execution
facts only; the default outputs are no-op frames and do not establish
conformance.

A non-default RadialBlur random reference case now receives all direct effect
parameters by property slot, including the duplicate `Strength` and `Offset`
names and the `Center` point. The separate PF Handle arena closed the null-base
write at RVA `0x2d52` and the later allocation stop at `0x9ff9`.
`omp_get_max_threads=1` then closed the divide-by-zero at RVA `0x5bac`.
The same full-size case now reaches the float4 bilinear sampler at RVA
`0x9e35`, where a generated x coordinate of about 9,874,418 causes an unmapped
read. Handle allocation failures are empty. Static analysis classifies this as
an unresolved render-context/ABI witness, not a manifest value or a proven
RadialBlur algorithm defect.

The current-AEX Smoother2 `legacy_case_0008_current_aex` reference now receives
all 15 editable parameters, including six RGBA color properties converted to
slot-qualified ARGB8. The unchanged AEX completes full-size Smart Render with
`render_error=0`. It is not exact: `max_diff=255` with 22,711 differing pixels.
This is a usable local actual-AEX differential, not an `AE exact` promotion.

## Plug-in setup sweep

Using the same worker and the local 2025 AEX set:

| AEX | `GLOBAL_SETUP` / `PARAMS_SETUP` |
| --- | --- |
| OLMBlur | success |
| OLMSmoother v1 | success |
| ColorKeep | success |
| DistanceGradation | success |
| OLMColorKey | success |
| OLMDirectionalBlur | success |
| OLMKiraKira | success |
| OLMRadialBlur | success |
| OLMSmoother2 | success |
| OLMToonDilate | success |

All ten 2025 AEX files now complete `GLOBAL_SETUP` and `PARAMS_SETUP` with
zero errors and no unsupported suite calls. The earlier common AEGP Utility
Suite blocker is closed.

## Operational decision

1. Use `scripts/run_aexcompat_reference.py` for full-frame 8bpc calibration.
2. Keep full-frame execution and dossier capture separate. Full-frame trace
   grows too quickly; trace inputs are rejected above 128x128 by default.
3. Treat AEXCompat as an internal execution oracle only after each plug-in has
   at least one Windows Software reference calibration with `max_diff=0`.
4. Keep property-slot addressing for manifests with duplicate visible names;
   bare ambiguous names fail closed.
5. Capture the RadialBlur RVA `0x9d80` sampler-entry values and caller
   render-context fields on AEXCompat and Windows before changing the port.
6. Use the now-completing Smoother2 current-AEX case to localize the first
   differing stage; do not tune the Mac output from the final PNG alone.
7. AEXCompat's PNG reference runner is currently ARGB8-only. It cannot close
   16bpc or 32bpc lanes
   until PF_Pixel16 and PF_PixelFloat worlds and suitable file I/O are added.
