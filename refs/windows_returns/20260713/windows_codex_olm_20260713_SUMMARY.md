# OLM Windows execution summary

## FACT

- Requests were extracted and processed sequentially under `runs\01_olmdirectionalblur` and `runs\02_olmsmoother2`.
- DirectionalBlur AEX: size `56832`, SHA-256 `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e`.
- Smoother2 shared AEX: size `192000`, SHA-256 `7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7`; no AEX pin was supplied in its manifest.
- After Effects 2025 and x64 CDB were used; both were closed after the incomplete second run.

## Runs

1. `powershell.exe -ExecutionPolicy Bypass -File .\run_alpha_fade_row755.ps1 -AexPath "C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMDirectionalBlur.aex" -CdbPath "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe" -AfterFxPath "C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe"` — exit `1`, `exact_bind_failure`, stage `runner_initialization`.
2. `powershell.exe -ExecutionPolicy Bypass -File "C:\olm_short\mac_codex_olm_20260713\runs\02_olmsmoother2\olmsmoother2_case0012_live_config_binding_20260713\run_olmsmoother2_case0012_live_config_binding_20260713.ps1" -PackageRoot "C:\olm_short\mac_codex_olm_20260713\runs\02_olmsmoother2\olmsmoother2_case0012_live_config_binding_20260713" -AfterFx "C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe" -Cdb "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe"` — host timeout `304s`; preserved `RETURN.json` is `exact_bind_failure`, stage `bind`.

## INFERENCE

Neither request produced `answered`; no partial result was promoted.

## Returns

- `return_01_olmdirectionalblur_20260713.zip`
- SHA-256: `708f9809b985bfc9ab6e82ec11a7eb92c6c3c2000ece16721db9668136389261`
- `return_02_olmsmoother2_20260713.zip`
- SHA-256: `db45a837c48fdf71907b9d50cbbe98fd1997bf65a965e87f94dffdbc63326b69`
