# OLM Windows native UCRT requests (AE-free)

These two hash-pinned request ZIPs run directly against the 64-bit AMD64
Windows `%WINDIR%\System32\ucrtbase.dll`. Neither request launches After
Effects, aerender, or another Adobe process.

## 1. DirectionalBlur + DistanceGradation (1,344 rows)

Extract `olm_runtime_trace_olm_math_ucrt_batch_20260814.zip`. From the directory
containing the extracted request directories, run this in 64-bit x64 Windows
PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\olm_runtime_trace_olm_math_ucrt_batch_20260814\run_olm_math_ucrt_batch.ps1 -OutputDir C:\olm-ucrt-return
```

Return this generated file without renaming or unpacking it:

`C:\olm-ucrt-return\olm_runtime_trace_olm_math_ucrt_batch_20260814_return_windows.zip`

## 2. RadialBlur Strength 290 (577 vectors)

Extract `olm_runtime_trace_olmradialblur_strength290_ucrt_math_20260814.zip`.
From the directory containing the extracted request directory, run this in
64-bit x64 Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\olm_runtime_trace_olmradialblur_strength290_ucrt_math_20260814\run_olmradialblur_strength290_ucrt_math.ps1 -OutputDir C:\olm-ucrt-return
```

Return this generated file without renaming or unpacking it:

`C:\olm-ucrt-return\olm_runtime_trace_olmradialblur_strength290_ucrt_math_20260814_return_windows.zip`

Run each request once. The Radial request refuses to overwrite an existing
return. Use an empty output directory if either named return already exists.
The returned native math words are evidence inputs only; they do not by
themselves authorize production admission.
