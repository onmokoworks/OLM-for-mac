param(
  [Parameter(Mandatory = $true)]
  [string]$HookScript,
  [string]$PackageRoot = '',
  [string]$WorkRoot = 'C:\Users\optim\Documents\Codex\2026-06-11\files-mentioned-by-the-user-olm\work',
  [string]$AfterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$Cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'

# The AE case, debugger process, and hook fragment deliberately share one run.
# $HookScript begins after RadialBlur.aex has loaded and must only contain the
# final-plane breakpoints/actions; it must not launch AE or render another case.
# The package launcher resumes AE after this fragment has armed its hooks.
if (-not $PackageRoot) {
  $PackageRoot = Split-Path -Parent $PSScriptRoot
}
$requestRelative = 'handoff\ae_pixel_validation_20260618\requests\ae_single_radialblur_case_0009_probe_20260701'
$runnerJsx = Join-Path $PackageRoot 'scripts\ae_render_single_case.jsx'
$requestDir = Join-Path $PackageRoot $requestRelative
$hookPath = if ([IO.Path]::IsPathRooted($HookScript)) { $HookScript } else { Join-Path $PackageRoot $HookScript }
$resultDir = Join-Path $WorkRoot 'olmradialblur_zoom_case0009_final_plane_typed_20260710'
$cdbScript = Join-Path $resultDir 'probe.cdb'
$stdoutFile = Join-Path $resultDir 'cdb_stdout.txt'
$stderrFile = Join-Path $resultDir 'cdb_stderr.txt'
$consoleFile = Join-Path $resultDir 'cdb_console.txt'
$singleLog = Join-Path $resultDir 'AE_SINGLE_CASE.log'

$requiredPaths = @(
  $AfterFx,
  $Cdb,
  $runnerJsx,
  $hookPath,
  (Join-Path $requestDir 'request_manifest.json'),
  (Join-Path $requestDir 'reference_manifest.json'),
  (Join-Path $requestDir 'input\case_0009_before_effects.png')
)
foreach ($requiredPath in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $requiredPath)) {
    throw "Missing package-local runner asset or tool: $requiredPath"
  }
}

Get-Process |
  Where-Object { $_.ProcessName -like 'AfterFX*' -or $_.ProcessName -like 'aerender*' -or $_.ProcessName -like 'cdb*' } |
  ForEach-Object { try { Stop-Process -Id $_.Id -Force -ErrorAction Stop } catch {} }

New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
Get-ChildItem -LiteralPath $resultDir -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = 'case_0009'
$env:OLM_AE_OUTPUT_DIR = $resultDir
$env:OLM_AE_LOG_PATH = $singleLog
$env:OLM_AE_RESULT_JSON = Join-Path $resultDir 'AE_SINGLE_CASE_RESULT.json'
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{}'
$env:OLM_AE_KEEP_OPEN = '0'

$prelude = @'
.logopen /t RESULT_DIR\cdb_trace.log
.symfix
.effmach amd64
.expr /s masm
sxi e06d7363
sxi 000006ba
sxi 887a0004
sxi 80000003
sxe ld:OLMRadialBlur.aex
sxe ld:OLMRadialBlur
g
.echo === MODULE_LOAD_RadialBlur ===
lm m OLMRadialBlur
.echo === FINAL_PLANE_HOOK_FRAGMENT_BEGIN ===
'@
$epilogue = @'
.echo === FINAL_PLANE_HOOK_FRAGMENT_END ===
.echo === RADIALBLUR_TYPED_RUN_END ===
q
'@
$cdbBody = $prelude.Replace('RESULT_DIR', $resultDir) + "`r`n" + (Get-Content -LiteralPath $hookPath -Raw) + "`r`n" + "g`r`n" + $epilogue
$cdbBody | Set-Content -LiteralPath $cdbScript -Encoding ASCII

$proc = Start-Process -FilePath $Cdb -ArgumentList @('-cf', $cdbScript, $AfterFx, '-r', $runnerJsx) -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -NoNewWindow -PassThru -Wait
$combined = @()
if (Test-Path $stdoutFile) { $combined += Get-Content -LiteralPath $stdoutFile }
if (Test-Path $stderrFile) { $combined += Get-Content -LiteralPath $stderrFile }
$combined | Set-Content -LiteralPath $consoleFile -Encoding UTF8
Write-Output ("=== RADIALBLUR_TYPED_CDB_EXIT_CODE={0} ===" -f $proc.ExitCode)
Write-Output ("request_id=olmradialblur_zoom_case0009_final_plane_typed_20260710 case_id=case_0009 hook_script={0}" -f $hookPath)
Select-String -Path $consoleFile -Pattern 'MODULE_LOAD_RadialBlur|FINAL_PLANE|RADIALBLUR_TYPED_RUN_END|Break instruction exception|WARNING' | Select-Object -First 160 | ForEach-Object { $_.Line }
