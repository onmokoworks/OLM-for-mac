# OLMRadialBlur Hook Liveness

Replace the body of `artifacts/hook_liveness.cdb` only if the Windows CDB
version does not support `bp /1`. The supplied fragment is unconditional on
purpose and uses each offset once. Run the package-local PowerShell launcher
with that hook file. Return the result JSON and both CDB/AE logs.
