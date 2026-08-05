# OLMRadialBlur Mac host boundary - 2026-07-18

## Decision

No source or host-bridge change is justified by the available binary evidence.
The internal PF32 chain is exact, but no Mac AE host output has been captured
for the same case and compared with the Windows AE Software reference.

## Exact missing boundary

For `case_0009` (Zoom, strength `1717`, center `[960,540]`, offset mode `1`,
offset `0`), the proven chain ends at the internal PF32 output frame:

- bytes: `33,177,600` (`1104x1800x4xfloat32`)
- SHA-256: `7de7d9700fddce9f77261fe3e81db8b89ffc88a06c897b866ffe512392562010`
- differing bytes/float words/pixels against the actual-AEX continuation oracle:
  `0/0/0`

The Mac source dispatches `PF_PixelFormat_ARGB128` to the `PF_PixelFloat`
path. That path reads the four host RGBA float channels directly and writes
the final four floats directly to the checked-out output world
(`mac/OLMRadialBlur/OLMRadialBlur.cpp:2033-2047`, `:2289-2347`). There is no
RadialBlur-specific PF32 conversion or post-write bridge in this lane. The
test seam captures caller-owned internal planes; it is not an AE output
capture.

Therefore the missing boundary is:

```text
Mac AE 32bpc Software render
  -> checked-out PF_EffectWorld / output-module FLOAT EXR
  -> raw RGBA float comparison with the matching Windows AE Software frame
```

It is not currently possible to classify the remaining difference as a
conversion, color-management, premultiplication, or output-module issue
without that same-run host artifact. The 2026-07-18 typed evidence also says
simple host rounding is not the dominant unresolved cause.

## Next executable local test

Build/install the current universal plug-in, then render a 32bpc Software
`case_0009` fixture with the exact reference parameters and the fixed float
output template. Capture both effect-on and effect-disabled controls, record
the loaded plug-in SHA-256, AE version, renderer, color settings, and output
module settings, then compare raw EXR samples before inspecting any residual:

```sh
xcodebuild -project mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj \
  -configuration Debug -sdk macosx build
python3 scripts/run_ae_single_case.py \
  --request-dir handoff/ae_pixel_validation_20260618/requests/ae_single_radialblur_case_0009_probe_20260701 \
  --case-id case_0009 \
  --output-mode exr_render_queue \
  --output-template 'OLM EXR 32 Float' \
  --output-dir /tmp/olmradialblur_case0009_mac_ae_20260718
```

The existing manifest is an 8bpc reference, so the local fixture must be
cloned to 32bpc while preserving its source image, parameter values, frame,
Software renderer, and color-management settings. Treat a missing control,
missing EXR, non-FLOAT/RGBA EXR, or missing loaded-binary identity as a
fail-closed result. Only after the control is valid should the effect-on EXR
be compared against the matching Windows float reference.

## Verification run

- `python3 tools/emulation/test_olmradialblur_sampler_contract_20260718.py`: pass
- `python3 tools/emulation/test_olmradialblur_prefill_eligibility_20260718.py`: pass; final frame `0` differing bytes
- `python3 tools/emulation/test_olmradialblur_case0009_pf32_residual_1313.py`: pass; internal frame exact
- `xcodebuild -project mac/OLMRadialBlur/Mac/OLMRadialBlur.xcodeproj -configuration Debug -sdk macosx build`: pass; universal arm64/x86_64
- `python3 tools/emulation/test_olmradialblur_typed_deep_render_20260718.py`: fail closed because its recorded production preblur baseline (`8e245bcc...`) does not match the current run (`fddeb494...`); this is an internal diagnostic baseline drift, not Mac AE host evidence.

No ledger entry was changed.
