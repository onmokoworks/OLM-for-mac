# OLMSmoother v1 16/32bpc expansion audit

Date: 2026-07-15

## Corrected decision

The first generated ZIP was not sendable: it contained the request, AEP, AEX,
and inputs, but no executable Windows runner or AE JSX. That archive is
superseded and must not be used.

The regenerated archive is an executable, fail-closed request package. It is
built and verified by
`scripts/package_olmsmoother_v1_bitdepth_request_20260715.py`, with focused
positive and archive-tampering tests in
`refs/scripts/smoke_package_olmsmoother_v1_bitdepth_request_20260715.py`.

## Executable package

The archive now includes:

- `run_windows.ps1`, which verifies every packaged contract and artifact hash,
  temporarily stages the exact v1 AEX in the per-user MediaCore directory,
  launches all six renders, validates output headers, emits a return manifest
  and return ZIP, and restores any pre-existing AEX.
- `scripts/render_olmsmoother_v1.jsx`, which deterministically builds each comp
  from the packaged before-effects input, binds exactly `OLM Smoother`, applies
  and reads back only the three v1 parameters, hashes that canonical returned
  readback, forces Software rendering and fixed
  color settings, requires the exact Output Module template, and renders one
  frame.
- Fixed color and output-template contracts, the source reference manifest,
  fixed AEP, fixed AEX, and all three hashed inputs.

The fixed AEP remains hash-gated source provenance. The JSX uses the permitted
deterministic-build route so it does not depend on mutable comp state inside the
AEP. The fixed render cell is `960x540` at 24 fps: both the three source PNGs
and the existing exact outputs are `960x540`, corresponding to the source
`1920x1080` comp at resolution factor `[2,2]`.

## Host and mapping audit

- `mac/OLMSmoother/Mac/OLMSmoother_port.cpp` has distinct 8-bit and 16-bit
  dispatches and forwards Smart Render bit depth from `extra->input->bitdepth`.
- The v1 parameter surface is `Use Color Key`, `Color Key`, and
  `Do Smooth Range`, mapped only to `SM_USE_KEY`, `SM_KEY_COLOR`, and
  `SM_TOLERANCE`. The runner and JSX do not reference OLMSmoother2.
- The Mac float callbacks are documented pass-through code with no proven
  Windows v1 analogue. Therefore the 32bpc lane remains probe-only even when a
  typed float32 OpenEXR is returned.

## Fail-closed boundary

The runner rejects missing AfterFX, runner/JSX, renderer, named Output Module
template, AEP, AEX, input, output, return metadata, or hash. It also rejects
effect identity or parameter-readback drift, non-Software rendering, color or
project-bpc drift, non-16-bit RGBA PNG in the 16bpc lane, non-float32,
compressed, or non-RGBA OpenEXR in the 32bpc lane, and parameter readback hash
mismatch.

The required Output Module templates are exactly `OLM PNG 16 RGBA` and
`OLM EXR 32 Float RGBA No Compression`. Missing templates fail closed; the
runner does not silently substitute a host default.

16bpc is exact-eligible only after a returned Windows render passes every gate
and is compared cross-host. 32bpc remains probe-only pending an independent Mac
boundary proof. This note does not change the existing 8bpc result and does not
modify the release ledger.

Build and verify:

```sh
python3 scripts/package_olmsmoother_v1_bitdepth_request_20260715.py
python3 refs/scripts/smoke_package_olmsmoother_v1_bitdepth_request_20260715.py
```
