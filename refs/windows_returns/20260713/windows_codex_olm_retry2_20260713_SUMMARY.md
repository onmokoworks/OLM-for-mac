# OLM Windows execution summary

All facts below are from the isolated run directories and supplied runner outputs. No run was mixed with another.

## FACTS

- Tool identity used for both requests: AfterFX 2025 file version `25.2`, SHA-256 `45b240ca8d2f7ca49eb23c1e025f74ae5239dcfe523a3205a594e9243e438efc`; x64 CDB file version `10.0.18362.1 (WinBuild.160101.0800)`, SHA-256 `b806eaea373d6add99fd9825a34820eb0779b9045cf71eecd7d070d58b8b6f6d`.
- DirectionalBlur AEX: `56832` bytes, SHA-256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- Smoother2 AEX: `192000` bytes, SHA-256 `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`.
- Exact runner command, DirectionalBlur: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\runs\\DirectionalBlur\\olmdirectionalblur_row755_nospace_jsx_retry_20260713\\run_alpha_fade_row755.ps1 -AexPath "C:\\Program Files\\Adobe\\Common\\Plug-ins\\7.0\\MediaCore\\OLM\\OLMDirectionalBlur.aex" -CdbPath "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\cdb.exe" -AfterFxPath "C:\\Program Files\\Adobe\\Adobe After Effects 2025\\Support Files\\AfterFX.exe" -WorkRoot .\\runs\\DirectionalBlur\\olmdirectionalblur_row755_nospace_jsx_retry_20260713\\execution`.
- DirectionalBlur exit code: `4`; status: `exact_bind_failure`; failure stage: `ae_pause`; reason: ready marker not written. Run ID: `dblur-row755-936a93a351144de2a7e337cf9a1e4ffd`.
- Exact runner command, Smoother2: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\\runs\\Smoother2\\olmsmoother2_case0012_live_config_binding_20260713\\run_olmsmoother2_case0012_live_config_binding_20260713.ps1 -PackageRoot .\\runs\\Smoother2\\olmsmoother2_case0012_live_config_binding_20260713 -WorkRoot .\\runs\\Smoother2\\olmsmoother2_case0012_live_config_binding_20260713\\execution -AfterFx "C:\\Program Files\\Adobe\\Adobe After Effects 2025\\Support Files\\AfterFX.exe" -Cdb "C:\\Program Files (x86)\\Windows Kits\\10\\Debuggers\\x64\\cdb.exe"`.
- Smoother2 exit code: `2`; status: `exact_bind_failure`; failure stage: `bind`; reason: all required bind/config/writer fields were missing. Run ID: `s2cfg_20260713095803550`.
- AfterFX and CDB were closed before each request and after each incomplete run.

## INFERENCES

- Neither request qualifies as `answered`: the package contracts require every typed witness in one run, and each runner returned `exact_bind_failure`.
- No `answered_partial` promotion was made.

## Preserved return archives

- `olm_directionalblur_alpha_fade_fullrender_row755_nospace_jsx_retry_20260713_return.zip`
- `olm_smoother2_case0012_live_config_binding_20260713_return.zip`
