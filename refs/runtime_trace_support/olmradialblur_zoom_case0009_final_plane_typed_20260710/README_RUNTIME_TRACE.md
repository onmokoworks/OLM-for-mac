# OLMRadialBlur Final-Plane Typed Witness

Run only `olmradialblur_zoom_case0009_final_plane_typed_20260710`.

Use one Windows AE Software `case_0009` render/debugger run. Capture primary
`(7,0)` and controls `(8,0),(24,0)` together. Fill the included return
template with typed inverse coordinates, four cell IDs, each cell's `+0xe`
RGBA float, corresponding `+0xf252`, bilinear weights, final alpha sum,
pre-byte alpha, observed RGBA8, and the exact hook/watchpoint artifact.

Final PNG bytes or package-local recomputation are not a valid substitute.
Return the completed JSON and the same-run debugger console/log artifact.

## Package-local runner

This package contains the AE runner and the exact `case_0009` request. Do not
use an older RadialBlur runner: that would turn the evidence into a mixed run.
The package-local hook file is deliberately a template, not a capture. Replace
its clearly marked section with the established final-plane CDB commands, then
run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\artifacts\run_olmradialblur_zoom_case0009_final_plane_typed_20260710.ps1 `
  -HookScript .\artifacts\final_plane_hook_fragment.cdb
```

The runner launches exactly one `AfterFX.exe -r scripts\ae_render_single_case.jsx`
under CDB, with the package-local `case_0009` request. The hook fragment begins
only after `RadialBlur.aex` has loaded. It must arm and collect all three typed
points. The package launcher then resumes the exact AE process once, so the
fragment must not quit CDB or launch a second render. Do not return template
placeholders as a capture.
