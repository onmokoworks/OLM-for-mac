# Windows 32bpc typed procedural fixture

Run this package on Windows from a clean AE session:

`powershell -ExecutionPolicy Bypass -File .\run_windows_typed_procedural_fixture_20260713.ps1 -AfterFX <AfterFX.exe> -ColorKeyAex <OLMColorKey.aex> -ToonDilateAex <OLMToonDilate.aex>`

The runner refuses to proceed if `AfterFX.exe` is already running. That is
intentional: the bundled JSX requires an empty project and empty render queue,
so each effect case is rendered in its own fresh AE process and the process is
stopped after the case completes.

Outputs:

- `run\cases\...\effect_no_effect_00000.exr`
- `run\cases\...\effect_effect_on_00000.exr`
- `run\return_manifest.json`
- `olm_windows_32bpc_typed_procedural_fixture_return.zip`

Cross-host compare after a macOS reference record exists:

`python compare_cross_host_typed_procedural_fixture.py <mac_record_dir_or_zip> <windows_return_dir_or_zip> --json`

The compare helper fails closed unless both hosts used the same bundled fixture
contract and both EXR outputs are raw-float-bit exact for `no_effect` and
`effect_on`.
