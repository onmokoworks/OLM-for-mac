param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [switch]$ParseOnly,
  [string]$TracePath = '',
  [string]$AexPath = 'C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\Plug-ins\Effects\DistanceGradation.aex',
  [string]$AfterFxPath = 'C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\AfterFX.exe',
  [string]$CdbPath = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'
$requestId = 'olmdistancegradation_8bpc_coordinate_liveness_census_20260715'
$expectedAexHash = 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
$cases = @('case_0001', 'case_0015', 'case_0029')
$inputHashes = @{
  case_0001 = '9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265'
  case_0015 = '9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265'
  case_0029 = '9d96a359d987774a398ec27e224650fda83fa00ae3c14bd04b87e2402ea34265'
}
$outputHashes = @{
  case_0001 = '7d8a37e51743efe9d9aa8dd8c70c220749039194c196828a5dc288885cd16f0f'
  case_0015 = '226fb67d4c527bc4aacc2f428cab9d6a8b1c5cb3c149f8abba21d20ab05c2ca7'
  case_0029 = 'a47f26dc730fb37280656511ef9835f6165f1997fa544f39410255094f923a58'
}
$runId = 'dg8census-' + [guid]::NewGuid().ToString('N')

function New-Failure([string]$reason, [object[]]$missing, [string]$lastObservation) {
  return [ordered]@{
    status = 'exact_bind_failure'
    kind = 'coordinate_liveness_census'
    request_id = $requestId
    exactness_claim = $false
    failure = [ordered]@{
      reason = $reason
      missing_fields = @($missing)
      last_observation = $lastObservation
    }
  }
}

function Parse-Fields([string]$line) {
  $fields = @{}
  foreach ($match in [regex]::Matches($line, '(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) {
    $fields[$match.Groups['key'].Value] = $match.Groups['value'].Value
  }
  return $fields
}

function Identity-Key([hashtable]$fields) {
  return "$($fields.run_id)|$($fields.ae_pid)|$($fields.module_base)|$($fields.aex_sha256)|$($fields.ae_version)|$($fields.renderer)|$($fields.project_bpc)|$($fields.case_id)|$($fields.input_sha256)|$($fields.output_sha256)"
}

function Convert-Int64([string]$value, [string]$fieldName) {
  $parsed = [int64]0
  if (-not [int64]::TryParse($value, [ref]$parsed)) { throw "$fieldName is not an Int64: $value" }
  return $parsed
}

function Convert-Int32([string]$value, [string]$fieldName) {
  $parsed = [int]0
  if (-not [int]::TryParse($value, [ref]$parsed)) { throw "$fieldName is not an Int32: $value" }
  return $parsed
}

function Parse-Trace([string]$path, [string]$caseId) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    return New-Failure 'missing CDB trace' @(("{0}:cdb_trace" -f $caseId)) ''
  }
  $coordinateRows = @()
  $neighborRows = @()
  $pf8Rows = @()
  $pf32Rows = @()
  $last = ''
  try {
    foreach ($line in Get-Content -LiteralPath $path) {
      $last = $line
      if ($line -match '^DG8_COORD\s+') {
        $fields = Parse-Fields $line
        if ($fields.case_id -eq $caseId) { $coordinateRows += $fields }
      } elseif ($line -match '^DG8_NEIGHBOR\s+') {
        $fields = Parse-Fields $line
        if ($fields.case_id -eq $caseId) { $neighborRows += $fields }
      } elseif ($line -match '^DG8_PF8_SUMMARY\s+') {
        $fields = Parse-Fields $line
        if ($fields.case_id -eq $caseId) { $pf8Rows += $fields }
      } elseif ($line -match '^DG8_PF32_SUMMARY\s+') {
        $fields = Parse-Fields $line
        if ($fields.case_id -eq $caseId) { $pf32Rows += $fields }
      }
    }
    if ($pf8Rows.Count -ne 1 -or $pf32Rows.Count -ne 1) {
      return New-Failure 'callback summaries must be unique' @(("{0}:PF8_summary_count" -f $caseId), ("{0}:PF32_summary_count" -f $caseId)) "pf8=$($pf8Rows.Count) pf32=$($pf32Rows.Count)"
    }
    $pf8 = $pf8Rows[0]
    $pf32 = $pf32Rows[0]
    $requiredIdentity = @('run_id', 'ae_pid', 'module_base', 'aex_sha256', 'ae_version', 'renderer', 'project_bpc', 'case_id', 'input_sha256', 'output_sha256')
    $missing = @()
    foreach ($key in $requiredIdentity) {
      if (-not $pf8.ContainsKey($key)) { $missing += ("{0}:PF8:{1}" -f $caseId, $key) }
      if (-not $pf32.ContainsKey($key)) { $missing += ("{0}:PF32:{1}" -f $caseId, $key) }
    }
    foreach ($key in @('total_count', 'min_x', 'max_x', 'min_y', 'max_y', 'target_neighborhood_count')) {
      if (-not $pf8.ContainsKey($key)) { $missing += ("{0}:PF8:{1}" -f $caseId, $key) }
    }
    if (-not $pf32.ContainsKey('count')) { $missing += ("{0}:PF32:count" -f $caseId) }
    if ($missing.Count -gt 0) { return New-Failure 'incomplete callback summary' $missing $last }

    $summaryIdentity = Identity-Key $pf8
    if ($summaryIdentity -ne (Identity-Key $pf32)) {
      return New-Failure 'PF8/PF32 identity mismatch' @(("{0}:callback_identity" -f $caseId)) $summaryIdentity
    }
    foreach ($row in @($coordinateRows) + @($neighborRows)) {
      foreach ($key in $requiredIdentity) {
        if (-not $row.ContainsKey($key)) {
          return New-Failure 'sample identity is incomplete' @(("{0}:sample:{1}" -f $caseId, $key)) $last
        }
      }
      if ((Identity-Key $row) -ne $summaryIdentity) {
        return New-Failure 'sample identity differs from summary' @(("{0}:sample_identity" -f $caseId)) (Identity-Key $row)
      }
      foreach ($key in @('callback_index', 'x', 'y', 'output_addr')) {
        if (-not $row.ContainsKey($key)) {
          return New-Failure 'sample fields are incomplete' @(("{0}:sample:{1}" -f $caseId, $key)) $last
        }
      }
    }

    $total = Convert-Int64 $pf8.total_count ("{0}:PF8_total_count" -f $caseId)
    $minX = Convert-Int32 $pf8.min_x ("{0}:min_x" -f $caseId)
    $maxX = Convert-Int32 $pf8.max_x ("{0}:max_x" -f $caseId)
    $minY = Convert-Int32 $pf8.min_y ("{0}:min_y" -f $caseId)
    $maxY = Convert-Int32 $pf8.max_y ("{0}:max_y" -f $caseId)
    $neighborCount = Convert-Int64 $pf8.target_neighborhood_count ("{0}:target_neighborhood_count" -f $caseId)
    $pf32Count = Convert-Int64 $pf32.count ("{0}:PF32_count" -f $caseId)
    $aePid = Convert-Int32 $pf8.ae_pid ("{0}:ae_pid" -f $caseId)
    $projectBpc = Convert-Int32 $pf8.project_bpc ("{0}:project_bpc" -f $caseId)
    if ($total -le 0 -or $neighborCount -lt 0 -or $neighborCount -gt $total -or $pf32Count -lt 0) {
      return New-Failure 'callback counts are outside the valid range' @(("{0}:callback_counts" -f $caseId)) "total=$total neighbor=$neighborCount pf32=$pf32Count"
    }
    if ($minX -gt $maxX -or $minY -gt $maxY) {
      return New-Failure 'callback coordinate envelope is inverted' @(("{0}:coordinate_envelope" -f $caseId)) "$minX,$maxX,$minY,$maxY"
    }
    if ($pf8.case_id -ne $caseId -or $pf8.run_id -eq '' -or $aePid -le 0 -or $projectBpc -ne 8 -or $pf8.renderer -ne 'Software' -or $pf8.aex_sha256 -ne $expectedAexHash -or $pf8.ae_version -ne '25.2x131' -or $pf8.input_sha256 -ne $inputHashes[$caseId] -or $pf8.output_sha256 -ne $outputHashes[$caseId] -or $pf8.module_base -notmatch '^0x[0-9a-fA-F]+$' -or $pf8.module_base -match '^0x0+$') {
      return New-Failure 'summary identity violates the request contract' @(("{0}:summary_identity" -f $caseId)) $summaryIdentity
    }

    $expectedCoordinateSamples = [int][Math]::Min([int64]16, $total)
    if ($coordinateRows.Count -ne $expectedCoordinateSamples) {
      return New-Failure 'first16 sample count is invalid' @(("{0}:first16" -f $caseId)) "total=$total first16=$($coordinateRows.Count)"
    }
    $coordinates = @()
    for ($index = 0; $index -lt $coordinateRows.Count; $index++) {
      $row = $coordinateRows[$index]
      $callbackIndex = Convert-Int64 $row.callback_index ("{0}:first16_callback_index" -f $caseId)
      $x = Convert-Int32 $row.x ("{0}:first16_x" -f $caseId)
      $y = Convert-Int32 $row.y ("{0}:first16_y" -f $caseId)
      if ($callbackIndex -ne $index -or $x -lt $minX -or $x -gt $maxX -or $y -lt $minY -or $y -gt $maxY -or $row.output_addr -notmatch '^0x[0-9a-fA-F]+$' -or $row.output_addr -match '^0x0+$') {
        return New-Failure 'first16 sample is invalid' @(("{0}:first16[{1}]" -f $caseId, $index)) ($row | ConvertTo-Json -Compress)
      }
      $coordinates += [ordered]@{ callback_index=$callbackIndex; x=$x; y=$y; output_addr=$row.output_addr }
    }

    $expectedNeighborSamples = [int][Math]::Min([int64]64, $neighborCount)
    if ($neighborRows.Count -ne $expectedNeighborSamples) {
      return New-Failure 'neighborhood sample count is invalid' @(("{0}:target_neighborhood_samples" -f $caseId)) "count=$neighborCount retained=$($neighborRows.Count)"
    }
    $neighbors = @()
    $previousNeighborIndex = [int64]-1
    $coordinateByIndex = @{}
    foreach ($coordinate in $coordinates) { $coordinateByIndex[[string]$coordinate.callback_index] = $coordinate }
    foreach ($row in $neighborRows) {
      $callbackIndex = Convert-Int64 $row.callback_index ("{0}:neighbor_callback_index" -f $caseId)
      $x = Convert-Int32 $row.x ("{0}:neighbor_x" -f $caseId)
      $y = Convert-Int32 $row.y ("{0}:neighbor_y" -f $caseId)
      if ($callbackIndex -le $previousNeighborIndex -or $callbackIndex -ge $total -or $x -lt 395 -or $x -gt 399 -or $y -lt 279 -or $y -gt 283 -or $row.output_addr -notmatch '^0x[0-9a-fA-F]+$' -or $row.output_addr -match '^0x0+$') {
        return New-Failure 'neighborhood sample is invalid' @(("{0}:target_neighborhood_sample" -f $caseId)) ($row | ConvertTo-Json -Compress)
      }
      $overlap = $coordinateByIndex[[string]$callbackIndex]
      if ($overlap -and ($overlap.x -ne $x -or $overlap.y -ne $y -or $overlap.output_addr -ne $row.output_addr)) {
        return New-Failure 'neighborhood/first16 overlap disagrees' @(("{0}:sample_overlap" -f $caseId)) ($row | ConvertTo-Json -Compress)
      }
      $neighbors += [ordered]@{ callback_index=$callbackIndex; x=$x; y=$y; output_addr=$row.output_addr }
      $previousNeighborIndex = $callbackIndex
    }

    return [ordered]@{
      status = 'answered'
      case_id = $caseId
      run_id = $pf8.run_id
      ae_pid = $aePid
      module_base = $pf8.module_base
      aex_sha256 = $pf8.aex_sha256
      ae_version = $pf8.ae_version
      renderer = $pf8.renderer
      project_bits_per_channel = $projectBpc
      input_sha256 = $pf8.input_sha256
      output_sha256 = $pf8.output_sha256
      pf8 = [ordered]@{
        total_count = $total
        min_x = $minX
        max_x = $maxX
        min_y = $minY
        max_y = $maxY
        first16 = @($coordinates)
        target_neighborhood_count = $neighborCount
        target_neighborhood_samples = @($neighbors)
        target_coordinate_observed = [bool](@($neighbors | Where-Object { $_.x -eq 397 -and $_.y -eq 281 }).Count)
        output_pointer_sample = @($coordinates | ForEach-Object { $_.output_addr })
      }
      pf32 = [ordered]@{ count = $pf32Count }
    }
  } catch {
    return New-Failure 'trace parsing failed closed' @(("{0}:typed_trace" -f $caseId)) $_.Exception.Message
  }
}

if ($ParseOnly) {
  if (-not $TracePath) { throw '-ParseOnly requires -TracePath' }
  $parsed = @($cases | ForEach-Object { Parse-Trace $TracePath $_ })
  $runIds = @($parsed | Where-Object { $_.status -eq 'answered' } | ForEach-Object { $_.run_id } | Select-Object -Unique)
  $caseIds = @($parsed | ForEach-Object { $_.case_id } | Sort-Object)
  $valid = @($parsed | Where-Object { $_.status -ne 'answered' }).Count -eq 0 -and $runIds.Count -eq 1 -and (($caseIds -join ',') -eq (($cases | Sort-Object) -join ','))
  $status = if ($valid) { 'parser_fixture_valid' } else { 'exact_bind_failure' }
  [ordered]@{ status=$status; kind='coordinate_liveness_census_parser_fixture'; request_id=$requestId; request_satisfied=$false; exactness_claim=$false; cases=$parsed } | ConvertTo-Json -Depth 16
  exit $(if ($valid) { 0 } else { 2 })
}

$work = Join-Path $WorkRoot $runId
New-Item -ItemType Directory -Force -Path $work | Out-Null
$returnPath = Join-Path $work 'RETURN_RUNTIME_TRACE.json'
$combinedTrace = Join-Path $work 'combined_cdb_trace.txt'
$sessionId = (Get-Process -Id $PID).SessionId
$currentCdb = $null
$currentAe = $null
$currentLauncher = $null
$currentContinue = $null

function Read-OrNull([string]$path) {
  if (Test-Path -LiteralPath $path -PathType Leaf) { return Get-Content -LiteralPath $path -Raw }
  return $null
}

function Stop-ActiveProcesses {
  if ($currentContinue -and -not (Test-Path -LiteralPath $currentContinue)) {
    Set-Content -LiteralPath $currentContinue -Value 'abort' -Encoding ASCII -ErrorAction SilentlyContinue
  }
  if ($currentCdb -and -not $currentCdb.HasExited) { Stop-Process -Id $currentCdb.Id -Force -ErrorAction SilentlyContinue }
  if ($currentAe -and -not $currentAe.HasExited) { Stop-Process -Id $currentAe.Id -Force -ErrorAction SilentlyContinue }
  foreach ($process in @(Get-TargetAfterFxProcesses)) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
  }
  if ($currentLauncher -and -not $currentLauncher.HasExited) {
    Stop-Process -Id $currentLauncher.Id -Force -ErrorAction SilentlyContinue
  }
  $deadline = (Get-Date).AddSeconds(10)
  while ((Get-Date) -lt $deadline -and @(Get-TargetAfterFxProcesses).Count -gt 0) { Start-Sleep -Milliseconds 250 }
}

function Finish([object]$body, [int]$code) {
  if ($code -ne 0) { Stop-ActiveProcesses }
  $json = $body | ConvertTo-Json -Depth 20
  $json | Set-Content -LiteralPath $returnPath -Encoding UTF8
  $json
  exit $code
}

function Get-LoadedModule {
  $matches = @()
  foreach ($process in Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {
    if ($process.SessionId -ne $sessionId) { continue }
    try {
      $module = $process.Modules | Where-Object { $_.FileName -ieq $AexPath } | Select-Object -First 1
      if ($module) { $matches += [pscustomobject]@{ Process=$process; Module=$module } }
    } catch {}
  }
  return @($matches)
}

function Get-TargetAfterFxProcesses {
  $matches = @()
  foreach ($process in Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {
    if ($process.SessionId -ne $sessionId) { continue }
    try {
      if ($process.Path -and [IO.Path]::GetFullPath($process.Path) -ieq $AfterFxPath) { $matches += $process }
    } catch {}
  }
  return @($matches)
}

try {
  $singleCaseJsx = Join-Path $PackageRoot 'scripts\ae_render_single_case.jsx'
  foreach ($path in @($AexPath, $AfterFxPath, $CdbPath, $singleCaseJsx)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "required file missing: $path" }
  }
  if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {
    throw 'After Effects must be fully closed before the census'
  }
  $AexPath = (Get-Item -LiteralPath $AexPath).FullName
  $AfterFxPath = (Get-Item -LiteralPath $AfterFxPath).FullName
  $CdbPath = (Get-Item -LiteralPath $CdbPath).FullName
  $actualAexHash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($actualAexHash -ne $expectedAexHash) { throw "AEX hash mismatch: $actualAexHash" }

  $results = @()
  foreach ($caseId in $cases) {
    if (@(Get-TargetAfterFxProcesses).Count -gt 0) { throw "$caseId started with a stale target AE process" }
    $caseWork = Join-Path $work $caseId
    New-Item -ItemType Directory -Force -Path $caseWork | Out-Null
    $inputPath = Join-Path $PackageRoot "request\input\${caseId}_before_effects.png"
    $actualInputHash = (Get-FileHash -LiteralPath $inputPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualInputHash -ne $inputHashes[$caseId]) { throw "$caseId input hash mismatch: $actualInputHash" }

    $ready = Join-Path $caseWork 'ae_ready.marker'
    $continue = Join-Path $caseWork 'ae_continue.marker'
    $aeLog = Join-Path $caseWork 'AE_SINGLE_CASE.log'
    $aeResultPath = Join-Path $caseWork 'AE_SINGLE_CASE_RESULT.json'
    $outputDir = Join-Path $caseWork 'output'
    $launcherStdout = Join-Path $caseWork 'afterfx_stdout.txt'
    $launcherStderr = Join-Path $caseWork 'afterfx_stderr.txt'
    $trace = Join-Path $caseWork 'cdb_trace.txt'
    $cdbStdout = Join-Path $caseWork 'cdb_stdout.txt'
    $cdbStderr = Join-Path $caseWork 'cdb_stderr.txt'
    $cdbScript = Join-Path $caseWork 'coordinate_census.cdb'

    $env:OLM_AE_REQUEST_DIR = Join-Path $PackageRoot 'request'
    $env:OLM_AE_CASE_ID = $caseId
    $env:OLM_AE_OUTPUT_DIR = $outputDir
    $env:OLM_AE_LOG_PATH = $aeLog
    $env:OLM_AE_RESULT_JSON = $aeResultPath
    $env:OLM_AE_READY_MARKER = $ready
    $env:OLM_AE_CONTINUE_MARKER = $continue
    $env:OLM_AE_PAUSE_BEFORE_RENDER = '1'
    $env:OLM_AE_PAUSE_TIMEOUT_SECONDS = '300'
    $env:OLM_AE_FORCE_SOFTWARE = '1'
    $env:OLM_AE_KEEP_OPEN = '0'
    $env:OLM_AE_FORCE_NEW_PROJECT = '1'

    $launcher = Start-Process -FilePath $AfterFxPath -ArgumentList @('-m', '-r', $singleCaseJsx) -RedirectStandardOutput $launcherStdout -RedirectStandardError $launcherStderr -PassThru
    $currentLauncher = $launcher
    $currentContinue = $continue
    $deadline = (Get-Date).AddSeconds(180)
    while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $ready -PathType Leaf)) { Start-Sleep -Milliseconds 250 }
    if (-not (Test-Path -LiteralPath $ready -PathType Leaf)) { throw "$caseId ready marker missing" }
    $readyText = Get-Content -LiteralPath $ready -Raw
    if ($readyText -notmatch 'effect_loaded=1' -or $readyText -notmatch 'parameters_applied=1') { throw "$caseId ready marker is incomplete: $readyText" }
    $readyVersion = [regex]::Match($readyText, 'ae_version=([^\s]+)')
    if (-not $readyVersion.Success) { throw "$caseId ready marker omitted AE version: $readyText" }
    $observedAeVersion = $readyVersion.Groups[1].Value
    if ($observedAeVersion -ne '25.2x131') { throw "$caseId AE build drift: $observedAeVersion" }

    $loaded = @()
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and $loaded.Count -ne 1) {
      $loaded = @(Get-LoadedModule)
      if ($loaded.Count -ne 1) { Start-Sleep -Milliseconds 250 }
    }
    if ($loaded.Count -ne 1) { throw "$caseId did not bind exactly one loaded AEX module" }
    $currentAe = $loaded[0].Process
    $module = $loaded[0].Module
    $loadedHash = (Get-FileHash -LiteralPath $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($loadedHash -ne $expectedAexHash) { throw "$caseId loaded AEX hash mismatch: $loadedHash" }
    $baseValue = $module.BaseAddress.ToInt64()
    $base = '0x{0:x}' -f $baseValue
    $pf8 = '0x{0:x}' -f ($baseValue + 0x1170870)
    $pf32 = '0x{0:x}' -f ($baseValue + 0x1170c90)
    $aePid = $currentAe.Id
    $caseAePid = $aePid
    $expectedOutputHash = $outputHashes[$caseId]

    $cdbText = @"
.effmach amd64
.expr /s masm
sxi 80000003
.logopen "$trace"
r @`$t0=0
r @`$t1=0
r @`$t2=0
r @`$t3=0
r @`$t4=0
r @`$t5=0
r @`$t6=0
r @`$t7=0
bp $pf8 ".if (@`$t0 == 0) { r @`$t1=@edx; r @`$t2=@edx; r @`$t3=@r8d; r @`$t4=@r8d }; .if (@edx < @`$t1) { r @`$t1=@edx }; .if (@edx > @`$t2) { r @`$t2=@edx }; .if (@r8d < @`$t3) { r @`$t3=@r8d }; .if (@r8d > @`$t4) { r @`$t4=@r8d }; .if (@`$t0 < 16) { .printf \"DG8_COORD run_id=$runId ae_pid=$aePid module_base=$base aex_sha256=$actualAexHash ae_version=$observedAeVersion renderer=Software project_bpc=8 case_id=$caseId input_sha256=$actualInputHash output_sha256=$expectedOutputHash callback_index=%I64u x=%d y=%d output_addr=0x%I64x\\n\", @`$t0, @edx, @r8d, poi(@rsp+0x28) }; .if (@edx >= 395 && @edx <= 399 && @r8d >= 279 && @r8d <= 283) { r @`$t6=@`$t6+1; .if (@`$t7 < 64) { .printf \"DG8_NEIGHBOR run_id=$runId ae_pid=$aePid module_base=$base aex_sha256=$actualAexHash ae_version=$observedAeVersion renderer=Software project_bpc=8 case_id=$caseId input_sha256=$actualInputHash output_sha256=$expectedOutputHash callback_index=%I64u x=%d y=%d output_addr=0x%I64x\\n\", @`$t0, @edx, @r8d, poi(@rsp+0x28); r @`$t7=@`$t7+1 } }; r @`$t0=@`$t0+1; gc"
bp $pf32 "r @`$t5=@`$t5+1; gc"
.echo DG8_CENSUS_BREAKPOINTS_ARMED
g
.printf "DG8_PF8_SUMMARY run_id=$runId ae_pid=$aePid module_base=$base aex_sha256=$actualAexHash ae_version=$observedAeVersion renderer=Software project_bpc=8 case_id=$caseId input_sha256=$actualInputHash output_sha256=$expectedOutputHash total_count=%I64u min_x=%d max_x=%d min_y=%d max_y=%d target_neighborhood_count=%I64u\n", @`$t0, @`$t1, @`$t2, @`$t3, @`$t4, @`$t6
.printf "DG8_PF32_SUMMARY run_id=$runId ae_pid=$aePid module_base=$base aex_sha256=$actualAexHash ae_version=$observedAeVersion renderer=Software project_bpc=8 case_id=$caseId input_sha256=$actualInputHash output_sha256=$expectedOutputHash count=%I64u\n", @`$t5
.logclose
q
"@
    $cdbText | Set-Content -LiteralPath $cdbScript -Encoding ASCII
    $currentCdb = Start-Process -FilePath $CdbPath -ArgumentList ('-cf "' + $cdbScript + '" -p ' + $aePid) -RedirectStandardOutput $cdbStdout -RedirectStandardError $cdbStderr -NoNewWindow -PassThru
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Date) -lt $deadline) {
      if ((Test-Path -LiteralPath $trace) -and ((Get-Content -LiteralPath $trace -Raw) -match 'DG8_CENSUS_BREAKPOINTS_ARMED')) { break }
      if ($currentCdb.HasExited) { break }
      Start-Sleep -Milliseconds 250
      $currentCdb.Refresh()
    }
    if (-not (Test-Path -LiteralPath $trace) -or -not ((Get-Content -LiteralPath $trace -Raw) -match 'DG8_CENSUS_BREAKPOINTS_ARMED')) { throw "$caseId CDB did not arm" }
    Set-Content -LiteralPath $continue -Value 'continue' -Encoding ASCII

    $deadline = (Get-Date).AddSeconds(300)
    while ((Get-Date) -lt $deadline -and -not $currentCdb.HasExited) { Start-Sleep -Milliseconds 250; $currentCdb.Refresh() }
    if (-not $currentCdb.HasExited) { throw "$caseId CDB/AE bounded run timed out" }
    $currentCdb = $null
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and -not (Test-Path -LiteralPath $aeResultPath -PathType Leaf)) { Start-Sleep -Milliseconds 250 }
    if (-not (Test-Path -LiteralPath $aeResultPath -PathType Leaf)) { throw "$caseId AE result missing" }
    $aeResult = Get-Content -LiteralPath $aeResultPath -Raw | ConvertFrom-Json
    if ($aeResult.status -ne 'ok' -or [int]$aeResult.project_bits_per_channel -ne 8) { throw "$caseId AE render did not finish at 8bpc" }
    if ($aeResult.project_working_space -ne 'None' -or [bool]$aeResult.project_linear_blending) { throw "$caseId color-management contract drift" }
    $aeLogText = Read-OrNull $aeLog
    if ($aeLogText -notmatch 'gpuAccelType=SOFTWARE') { throw "$caseId SOFTWARE renderer was not confirmed" }
    if ([string]$aeResult.ae_version -ne $observedAeVersion -or $observedAeVersion -ne '25.2x131') { throw "$caseId AE version drift: $($aeResult.ae_version) / $observedAeVersion" }
    $outputPath = [string]$aeResult.output_png
    if (-not (Test-Path -LiteralPath $outputPath -PathType Leaf)) { throw "$caseId output PNG missing" }
    $actualOutputHash = (Get-FileHash -LiteralPath $outputPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualOutputHash -ne $outputHashes[$caseId]) { throw "$caseId output hash mismatch: $actualOutputHash" }

    $parsed = Parse-Trace $trace $caseId
    if ($parsed.status -ne 'answered') { Finish $parsed 2 }
    if ($parsed.run_id -ne $runId -or $parsed.ae_pid -ne $aePid -or $parsed.module_base -ne $base -or $parsed.aex_sha256 -ne $actualAexHash) {
      throw "$caseId parsed callback identity differs from the loaded module"
    }
    $parsed['input_sha256'] = $actualInputHash
    $parsed['output_sha256'] = $actualOutputHash
    $parsed['ae_result'] = $aeResult
    $parsed['raw_logs'] = [ordered]@{
      cdb_trace = Read-OrNull $trace
      cdb_stdout = Read-OrNull $cdbStdout
      cdb_stderr = Read-OrNull $cdbStderr
      ae_log = $aeLogText
      ae_result = Read-OrNull $aeResultPath
      launcher_stdout = Read-OrNull $launcherStdout
      launcher_stderr = Read-OrNull $launcherStderr
    }
    $results += $parsed
    Get-Content -LiteralPath $trace | Add-Content -LiteralPath $combinedTrace
    $deadline = (Get-Date).AddSeconds(30)
    while ((Get-Date) -lt $deadline -and (Get-Process -Id $caseAePid -ErrorAction SilentlyContinue)) { Start-Sleep -Milliseconds 250 }
    if (Get-Process -Id $caseAePid -ErrorAction SilentlyContinue) { throw "$caseId After Effects did not exit" }
    $currentAe = $null
    $currentLauncher = $null
    $currentContinue = $null
  }

  $resultRunIds = @($results | ForEach-Object { $_.run_id } | Select-Object -Unique)
  $resultCaseIds = @($results | ForEach-Object { $_.case_id } | Sort-Object)
  if ($results.Count -ne $cases.Count -or $resultRunIds.Count -ne 1 -or $resultRunIds[0] -ne $runId -or (($resultCaseIds -join ',') -ne (($cases | Sort-Object) -join ','))) {
    throw 'final three-case identity set is incomplete or mixed'
  }
  Finish ([ordered]@{
    status = 'answered'
    kind = 'coordinate_liveness_census'
    request_id = $requestId
    exactness_claim = $false
    run_id = $runId
    aex_sha256 = $actualAexHash
    renderer = 'Software'
    project_bits_per_channel = 8
    cases = @($results)
    combined_cdb_trace = Read-OrNull $combinedTrace
  }) 0
} catch {
  Finish (New-Failure 'bounded census execution failed' @('complete_three_case_census') $_.Exception.Message) 2
}
