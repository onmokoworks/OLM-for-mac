param(
  [ValidateSet('field', 'source', 'writer')]
  [string]$Site = 'field',
  [ValidateRange(0, 10000)]
  [int]$X = 6,
  [ValidateRange(0, 10000)]
  [int]$Y = 40,
  [switch]$UseHardwareBreakpoints,
  [string]$PackageRoot = '',
  [string]$WorkRoot = 'C:\Users\optim\Documents\Codex\2026-06-11\files-mentioned-by-the-user-olm\work'
)

$ErrorActionPreference = 'Stop'

# One process, one target address, and one downstream breakpoint per run.
$caseId = 'olmdistancegradation_extended__case_0010'
$rowBytes = 0x3c00
$pixelSize = 8
$afterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe'
$cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
if (-not $PackageRoot) {
  $PackageRoot = Split-Path -Parent $PSScriptRoot
}
$requestRelative = 'handoff\ae_pixel_validation_20260618\requests\ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625'
$runnerJsx = Join-Path $PackageRoot 'scripts\ae_render_single_case.jsx'
$requestDir = Join-Path $PackageRoot $requestRelative
$tag = "case0010_${Site}_${X}_${Y}"
$resultDir = Join-Path $WorkRoot "distancegradation_compose_single_site_followup_20260710_$tag"
$cdbScript = Join-Path $resultDir 'probe.cdb'
$stdoutFile = Join-Path $resultDir 'cdb_stdout.txt'
$stderrFile = Join-Path $resultDir 'cdb_stderr.txt'
$consoleFile = Join-Path $resultDir 'cdb_console.txt'
$singleLog = Join-Path $resultDir 'AE_SINGLE_CASE.log'

$requiredPaths = @(
  $runnerJsx,
  (Join-Path $requestDir 'request_manifest.json'),
  (Join-Path $requestDir 'reference_manifest.json'),
  (Join-Path $requestDir 'input\olm_bitdepth_16bpc_normalized_exact_20260625__software_16bpc__fr24__olmdistancegradation_extended__case_0010_before_effects.png')
)
foreach ($requiredPath in $requiredPaths) {
  if (-not (Test-Path -LiteralPath $requiredPath)) {
    throw "Missing packaged runner/request asset: $requiredPath"
  }
}

Get-Process |
  Where-Object { $_.ProcessName -like 'AfterFX*' -or $_.ProcessName -like 'aerender*' -or $_.ProcessName -like 'cdb*' } |
  ForEach-Object { try { Stop-Process -Id $_.Id -Force -ErrorAction Stop } catch {} }

New-Item -ItemType Directory -Force -Path $resultDir | Out-Null
Get-ChildItem -LiteralPath $resultDir -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = $caseId
$env:OLM_AE_OUTPUT_DIR = $resultDir
$env:OLM_AE_LOG_PATH = $singleLog
$env:OLM_AE_RESULT_JSON = Join-Path $resultDir 'AE_SINGLE_CASE_RESULT.json'
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{}'

$siteOffset = switch ($Site) {
  'field' { '117057d' }
  'source' { '11705f1' }
  'writer' { '1170814' }
}
$siteCommand = switch ($Site) {
  'field' {
    '.if (@rdi == @$t1) { .echo === EXACT_SITE_HIT ===; .echo site=field gate=RDI==target_output; .printf "rdi=%p target_output=%p x=%u y=%u\n", @rdi, @$t1, @r9d, @r8d; r; .printf "field_rcx=%p\n", @rcx; dw @rcx L8; .printf "field_base_from_static=%p field_rowbytes_ptr=%p field_pixel_size=8\n", @rcx-({Y}*0x3c00)-({X}*8), @r10+0x20; r xmm0; r xmm1; r xmm2; r xmm4; r xmm5; .echo === EXACT_SITE_CONTINUE ===; gc } .else { gc }'
  }
  'source' {
    '.if (@rdi == @$t1) { .echo === EXACT_SITE_HIT ===; .echo site=source gate=RDI==target_output; .printf "rdi=%p target_output=%p x=%u y=%u\n", @rdi, @$t1, @r9d, @r8d; r; .printf "source_rdx=%p\n", @rdx; dw @rdx L8; .printf "source_base_from_static=%p source_rowbytes_ptr=%p source_pixel_size=8\n", @rdx-({Y}*0x3c00)-({X}*8), @r10+0x20; r xmm0; r xmm1; r xmm2; r xmm6; r xmm7; r xmm11; r xmm12; r xmm13; .echo === EXACT_SITE_CONTINUE ===; gc } .else { gc }'
  }
  'writer' {
    '.if (@rdi == @$t1) { .echo === EXACT_SITE_HIT ===; .echo site=writer gate=RDI==target_output; .printf "rdi=%p target_output=%p\n", @rdi, @$t1; r; .printf "writer_output=%p final_store_words=\n", @rdi; dw @rdi L4; r xmm1; r xmm4; r xmm5; r xmm6; .echo === EXACT_SITE_CONTINUE ===; gc } .else { gc }'
  }
}
$siteCommand = $siteCommand.Replace('{X}', [string]$X).Replace('{Y}', [string]$Y)
$entryBreakpoint = if ($UseHardwareBreakpoints) { 'ba e 1' } else { 'bp' }
$siteBreakpoint = if ($UseHardwareBreakpoints) { 'ba e 1' } else { 'bp' }
$cdbBody = @'
.logopen /t RESULT_DIR\cdb_trace.log
.symfix
.effmach amd64
.expr /s masm
sxi e06d7363
sxi 000006ba
sxi 887a0004
sxi 80000003
sxe ld:DistanceGradation.aex
sxe ld:DistanceGradation
g
.echo === MODULE_LOAD_DistanceGradation ===
lm m DistanceGradation
r @$t0 = 0
r @$t1 = 0
ENTRY_BREAKPOINT DistanceGradation+0x1170480 ".if (@$t0 == 0) { .echo === ENTRY_BASE_WITNESS ===; .printf \"entry_x=%u entry_y=%u output_arg=%p source_arg=%p\n\", @edx, @r8d, poi(@rsp+0x28), @r9; r @$t0 = poi(@rsp+0x28) - @r8*0x3c00 - @edx*8; r @$t1 = @$t0 + {Y}*0x3c00 + {X}*8; .printf \"output_base=%p target_output=%p target_xy=({X},{Y}) rowbytes=0x3c00 pixel_size=8\n\", @$t0, @$t1; bc 0; gc } .else { gc }"
SITE_BREAKPOINT DistanceGradation+0xSITE_OFFSET "SITE_COMMAND"
.echo === SINGLE_SITE_BPS_ARMED site=SITE_NAME xy=(X,Y) ===
bl
sxd ld:DistanceGradation.aex
sxd ld:DistanceGradation
g
.echo === SINGLE_SITE_END ===
q
'@
$cdbBody = $cdbBody.Replace('RESULT_DIR', $resultDir).Replace('ENTRY_BREAKPOINT', $entryBreakpoint).Replace('SITE_BREAKPOINT', $siteBreakpoint).Replace('SITE_OFFSET', $siteOffset).Replace('SITE_COMMAND', $siteCommand).Replace('{X}', [string]$X).Replace('{Y}', [string]$Y).Replace('SITE_NAME', $Site)
$cdbBody | Set-Content -LiteralPath $cdbScript -Encoding ASCII

$proc = Start-Process -FilePath $cdb -ArgumentList @('-cf', $cdbScript, $afterFx, '-r', $runnerJsx) -RedirectStandardOutput $stdoutFile -RedirectStandardError $stderrFile -NoNewWindow -PassThru -Wait
$combined = @()
if (Test-Path $stdoutFile) { $combined += Get-Content -LiteralPath $stdoutFile }
if (Test-Path $stderrFile) { $combined += Get-Content -LiteralPath $stderrFile }
$combined | Set-Content -LiteralPath $consoleFile -Encoding UTF8
Write-Output ("=== {0} CDB_EXIT_CODE={1} ===" -f $tag, $proc.ExitCode)
Write-Output ("hardware_breakpoints={0}" -f [bool]$UseHardwareBreakpoints)
Select-String -Path $consoleFile -Pattern 'ENTRY_BASE_WITNESS|output_base=|EXACT_SITE_HIT|SINGLE_SITE_END|Break instruction exception|WARNING' | Select-Object -First 120 | ForEach-Object { $_.Line }
