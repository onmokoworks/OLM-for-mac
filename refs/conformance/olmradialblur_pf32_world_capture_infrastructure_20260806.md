# OLMRadialBlur PF32 diagnostic world capture

`OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE` is intentionally undefined in the normal
project. A diagnostic build with that macro reads an explicit, pre-created
destination from `OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE_DIR` and captures only the
canonical PF32 case0009 SmartRender path.

Each stage emits metadata plus `height * rowbytes` raw bytes in top-to-bottom
row order. The raw format is `PF_PixelFloat` ARGB and retains every positive
rowbytes padding byte. Metadata records dimensions, rowbytes, extent hint,
pixel format, memory channel order, and byte count. Existing target files,
unsupported parameters/formats/geometries, missing destinations, and negative
or short rowbytes fail closed.

Hostless verification:

```sh
python3 tools/emulation/test_olmradialblur_pf32_world_capture_infrastructure_20260806.py
```

## Diagnostic build/install/runner plan

1. Clone the normal Xcode configuration as a temporary diagnostic
   configuration and add `OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE=1` to that
   configuration only.
2. Build Universal and verify signatures/architectures without replacing the
   installed normal bundle.
3. Stop AE, back up the installed bundle, install the hash-recorded diagnostic
   bundle, and create a new empty capture directory.
4. Export `OLM_RADIALBLUR_DIAGNOSTIC_CAPTURE_DIR` into the AE launch environment,
   start one Software-render AE instance, attest the loaded module hash, and run
   the pinned case0009 PF32 runner once.
5. Require exactly `input/output.{json,argb128.rows}` and the two EXRs. Compare
   captured input against the compact control mapping, captured output against
   local production replay and effect EXR, respecting recorded rowbytes.
6. Stop AE and restore the backed-up normal bundle before any routine work.

No diagnostic bundle is installed by this change.
