param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [string]$AexPath = '',
  [string]$AfterFxPath = '',
  [string]$CdbPath = '',
  [switch]$ParseOnly,
  [string]$TracePath = '',
  [string]$IdentityPath = ''
)

$ErrorActionPreference = 'Stop'
$contractPath = Join-Path $PackageRoot 'witness-contract.json'
$runtimePath = Join-Path $PackageRoot 'scripts\witness_runtime.py'
if (!(Test-Path -LiteralPath $contractPath -PathType Leaf)) { throw "missing contract: $contractPath" }
if (!(Test-Path -LiteralPath $runtimePath -PathType Leaf)) { throw "missing runtime: $runtimePath" }
$contract = Get-Content -LiteralPath $contractPath -Raw | ConvertFrom-Json

if ($ParseOnly) {
  if (!$TracePath -or !$IdentityPath) { throw '-ParseOnly requires -TracePath and -IdentityPath' }
  $parseOutput = Join-Path ([IO.Path]::GetTempPath()) ("windows_witness_parse_" + [guid]::NewGuid().ToString('N') + '.json')
  & py -3 $runtimePath validate --contract $contractPath --trace $TracePath --identity $IdentityPath --output $parseOutput
  $code = $LASTEXITCODE
  if (Test-Path -LiteralPath $parseOutput) { Get-Content -LiteralPath $parseOutput -Raw; Remove-Item $parseOutput -Force -ErrorAction SilentlyContinue }
  exit $code
}

if (!$AexPath) { $AexPath = [string]$contract.plugin.default_aex_path }
if (!$AfterFxPath) { $AfterFxPath = [string]$contract.host.afterfx_path }
if (!$CdbPath) { $CdbPath = [string]$contract.host.cdb_path }
$runId = ([string]$contract.run_id_prefix) + '-' + ([guid]::NewGuid().ToString('N'))
$work = Join-Path $WorkRoot $runId
New-Item -ItemType Directory -Force -Path $work | Out-Null
$work = (Get-Item -LiteralPath $work).FullName
$combinedTrace = Join-Path $work 'combined_cdb_trace.txt'
$identityPath = Join-Path $work 'runtime_identity.json'
$statusPath = Join-Path $work 'validation_status.json'
$launchOut = Join-Path $work 'afterfx_launcher_stdout.txt'
$launchErr = Join-Path $work 'afterfx_launcher_stderr.txt'
$processDiagnostics = Join-Path $work 'afterfx_process_diagnostics.json'
$bootstrapCdbScriptEvidence = Join-Path $work 'afterfx_bootstrap.cdb'
$bootstrapCdbTraceEvidence = Join-Path $work 'afterfx_bootstrap_cdb_trace.txt'
$launchWrapperEvidence = Join-Path $work 'afterfx_launch_wrapper.cmd'
$queueLaunchEvidence = Join-Path $work 'launched_queue.jsx'
$queuePath = Join-Path $PackageRoot ([string]$contract.queue).Replace('/', '\')
$sessionId = (Get-Process -Id $PID).SessionId
$launch = $null
$cdb = $null
$launchStarted = $false
$launchArguments = $null
$launchArgumentValues = @()
$boundPid = $null
$boundBase = $null
$launchDir = $null
$queueBootstrap = $null
$queueLaunch = $null
$bootstrapCdbScript = $null
$bootstrapCdbTrace = $null
$launchWrapper = $null
$normalizedQueuePath = $null
$observedCommandLine = $null
$bootstrapObservedMarker = $false
$bootstrapPluginLoadClaimed = $false
$queueBootstrapObserved = $false
$queueBootstrapBinding = $null
$bootstrapAePid = $null
$activeCdbTrace = $null
$activeCdbTraceEvidence = $null

function Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last) {
  [ordered]@{
    schema_version = 1
    status = 'exact_bind_failure'
    request_id = [string]$contract.request_id
    failure = [ordered]@{stage=$stage; reason=$reason; missing_fields=@($missing); last_observation=$last}
  }
}

function ConvertTo-WindowsCommandLineArgument([string]$value) {
  if ($null -eq $value) { throw 'Windows command-line arguments may not be null' }
  if ($value.Length -gt 0 -and $value -notmatch '[\s"]') { return $value }
  $builder = New-Object System.Text.StringBuilder
  [void]$builder.Append('"')
  $backslashes = 0
  foreach ($character in $value.ToCharArray()) {
    if ($character -eq '\') { $backslashes++; continue }
    if ($character -eq '"') {
      [void]$builder.Append(('\' * (($backslashes * 2) + 1)))
      [void]$builder.Append('"')
      $backslashes = 0
      continue
    }
    if ($backslashes -gt 0) { [void]$builder.Append(('\' * $backslashes)); $backslashes = 0 }
    [void]$builder.Append($character)
  }
  if ($backslashes -gt 0) { [void]$builder.Append(('\' * ($backslashes * 2))) }
  [void]$builder.Append('"')
  return $builder.ToString()
}

function Join-WindowsCommandLine([object[]]$values) {
  return (($values | ForEach-Object { ConvertTo-WindowsCommandLineArgument ([string]$_) }) -join ' ')
}

function Read-QueueBootstrapBinding([string]$path) {
  $lines = @(Get-Content -LiteralPath $path)
  if (@($lines | Where-Object { $_ -ceq 'WITNESS_QUEUE_BOOTSTRAP' }).Count -ne 1) {
    throw 'queue bootstrap marker header is missing or duplicated'
  }
  $values = [ordered]@{}
  foreach ($line in $lines) {
    if ($line -ceq 'WITNESS_QUEUE_BOOTSTRAP') { continue }
    if ($line -notmatch '^([^=]+)=(.*)$') { throw "malformed queue bootstrap marker line: $line" }
    $key = [string]$Matches[1]
    if ($values.Contains($key)) { throw "duplicate queue bootstrap marker field: $key" }
    $values[$key] = [string]$Matches[2]
  }
  return [pscustomobject]$values
}

function Get-AfterFxState {
  @(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
      $_.SessionId -eq $sessionId -and $_.ExecutablePath -and
      [IO.Path]::GetFullPath($_.ExecutablePath) -ieq $AfterFxPath
    } |
    ForEach-Object {
      [ordered]@{pid=[int]$_.ProcessId; parent_pid=[int]$_.ParentProcessId; session_id=[int]$_.SessionId; path=$_.ExecutablePath; command_line=$_.CommandLine}
    })
}

function Stop-WitnessProcesses {
  foreach ($case in @($contract.cases)) {
    $ready = Join-Path $work ("ready_" + $case.id + '.marker')
    $continue = Join-Path $work ("continue_" + $case.id + '.marker')
    if ((Test-Path -LiteralPath $ready) -and !(Test-Path -LiteralPath $continue)) {
      Set-Content -LiteralPath $continue -Value 'abort' -Encoding ASCII -ErrorAction SilentlyContinue
    }
  }
  if ($cdb -and !$cdb.HasExited) { Stop-Process -Id $cdb.Id -Force -ErrorAction SilentlyContinue }
  if ($launch -and !$launch.HasExited) { Stop-Process -Id $launch.Id -Force -ErrorAction SilentlyContinue }
  if ($launchStarted) {
    foreach ($state in @(Get-AfterFxState)) {
      Stop-Process -Id $state.pid -Force -ErrorAction SilentlyContinue
      Wait-Process -Id $state.pid -Timeout 10 -ErrorAction SilentlyContinue
    }
  }
}

function Copy-WitnessLaunchEvidence {
  foreach ($pair in @(
    [pscustomobject]@{Source=$bootstrapCdbScript; Destination=$bootstrapCdbScriptEvidence}
    [pscustomobject]@{Source=$bootstrapCdbTrace; Destination=$bootstrapCdbTraceEvidence}
    [pscustomobject]@{Source=$launchWrapper; Destination=$launchWrapperEvidence}
    [pscustomobject]@{Source=$queueLaunch; Destination=$queueLaunchEvidence}
    [pscustomobject]@{Source=$queueBootstrap; Destination=(Join-Path $work 'queue_bootstrap.log')}
    [pscustomobject]@{Source=$activeCdbTrace; Destination=$activeCdbTraceEvidence}
  )) {
    if ($pair.Source -and $pair.Destination -and (Test-Path -LiteralPath $pair.Source -PathType Leaf)) {
      Copy-Item -LiteralPath $pair.Source -Destination $pair.Destination -Force -ErrorAction SilentlyContinue
    }
  }
}

function Finish([object]$body, [int]$code) {
  [ordered]@{
    launch_pid = $(if ($launch) { [int]$launch.Id } else { $null })
    launch_arguments = $launchArguments
    launch_argument_values = @($launchArgumentValues)
    normalized_queue_path = $normalizedQueuePath
    observed_afterfx_command_line = $observedCommandLine
    bootstrap_scope = 'direct AfterFX.exe initial breakpoint'
    bootstrap_host_image_marker_observed = [bool]$bootstrapObservedMarker
    bootstrap_plugin_load_claimed = [bool]$bootstrapPluginLoadClaimed
    queue_bootstrap_marker_observed = [bool]$queueBootstrapObserved
    queue_bootstrap_binding = $queueBootstrapBinding
    session_id = [int]$sessionId
    observed_afterfx = @(Get-AfterFxState)
  } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $processDiagnostics -Encoding UTF8 -ErrorAction SilentlyContinue
  if ($code -ne 0) { Stop-WitnessProcesses }
  Copy-WitnessLaunchEvidence
  $body | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statusPath -Encoding UTF8
  & py -3 $runtimePath bundle --contract $contractPath --status $statusPath --work $work
  $bundleCode = $LASTEXITCODE
  $returnJson = Join-Path $work ([string]$contract.return_bundle.json_name)
  $returnZip = Join-Path $work ([string]$contract.return_bundle.zip_name)
  if ($code -eq 0) { Stop-WitnessProcesses }
  if ($launchDir) { Remove-Item -LiteralPath $launchDir -Recurse -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $returnJson) { Get-Content -LiteralPath $returnJson -Raw }
  Write-Host "work_directory=$work"
  if (Test-Path -LiteralPath $returnZip) { Write-Host "return_zip=$returnZip" }
  if ($code -eq 0 -and $bundleCode -eq 0) { exit 0 }
  exit 2
}

function Render-Cdb([object]$case, [string]$trace, [Int64]$baseValue, [string]$hash) {
  $templatePath = Join-Path $PackageRoot ([string]$case.package_cdb_template).Replace('/', '\')
  $text = Get-Content -LiteralPath $templatePath -Raw
  $fixed = [ordered]@{
    RUN_ID=$runId; AE_PID=[string]$boundPid; MODULE_BASE=$boundBase; AEX_SHA256=$hash
    PROJECT_BPC=[string]$contract.project.bits_per_channel; RENDERER=[string]$contract.project.renderer
    CASE_ID=[string]$case.id; TRACE_PATH=$trace
  }
  foreach ($pair in $fixed.GetEnumerator()) { $text = $text.Replace('{{' + $pair.Key + '}}', [string]$pair.Value) }
  foreach ($property in $case.template_values.psobject.Properties) {
    $text = $text.Replace('{{CASE_VALUE:' + $property.Name + '}}', [string]$property.Value)
  }
  foreach ($property in $case.addresses.psobject.Properties) {
    $rvaText = [string]$property.Value
    $rva = [Convert]::ToInt64($rvaText.Substring(2), 16)
    $address = '0x{0:x}' -f ($baseValue + $rva)
    $text = $text.Replace('{{ADDRESS:' + $property.Name + '}}', $address)
  }
  if ($text -match '\{\{[^{}]+\}\}') { throw "unresolved CDB placeholder: $($Matches[0])" }
  return $text
}

foreach ($path in @($AexPath, $AfterFxPath, $CdbPath, $queuePath)) {
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { Finish (Failure 'preflight' "required file missing: $path" @('preflight_file') '') 2 }
}
if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {
  Finish (Failure 'desktop_launch' 'After Effects must be fully closed before this run' @('fresh_AfterFX_process') '') 2
}
$AexPath = (Get-Item -LiteralPath $AexPath).FullName
$AfterFxPath = (Get-Item -LiteralPath $AfterFxPath).FullName
$CdbPath = (Get-Item -LiteralPath $CdbPath).FullName
$PackageRoot = (Get-Item -LiteralPath $PackageRoot).FullName
$hash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne [string]$contract.plugin.aex_sha256) {
  Finish (Failure 'module_hash' 'AEX hash does not match the witness contract' @('expected_aex_sha256') "actual=$hash") 2
}

$env:WINDOWS_WITNESS_WORK_ROOT = $work
$env:WINDOWS_WITNESS_RUN_ID = $runId
$env:WINDOWS_WITNESS_PACKAGE_ROOT = $PackageRoot
$env:OLM_AE_PAUSE_BEFORE_RENDER = '1'
$env:OLM_AE_PAUSE_TIMEOUT_SECONDS = '300'
$env:OLM_AE_FORCE_SOFTWARE = '1'
foreach ($property in $contract.project.environment.psobject.Properties) {
  [Environment]::SetEnvironmentVariable($property.Name, [string]$property.Value, 'Process')
}
$shortId = [guid]::NewGuid().ToString('N').Substring(0, 12)
$launchDir = Join-Path $env:PUBLIC ('OLMWitness\w_' + $shortId)
New-Item -ItemType Directory -Force -Path $launchDir | Out-Null
$launchDir = (Get-Item -LiteralPath $launchDir).FullName
$queueLaunch = Join-Path $launchDir 'queue.jsx'
$queueBootstrap = Join-Path $launchDir 'queue_bootstrap.log'
$bootstrapCdbScript = Join-Path $launchDir 'boot.cdb'
$bootstrapCdbTrace = Join-Path $launchDir 'boot.log'
$launchWrapper = Join-Path $launchDir 'launch.cmd'
Copy-Item -LiteralPath $queuePath -Destination $queueLaunch -Force
Remove-Item -LiteralPath $queueBootstrap -Force -ErrorAction SilentlyContinue
if ($queueLaunch -match '\s') { Finish (Failure 'path_preflight' 'short JSX launch path contains whitespace' @('no_space_queue_path') $queueLaunch) 2 }
$normalizedQueuePath = [IO.Path]::GetFullPath($queueLaunch)
$queueHash = (Get-FileHash -LiteralPath $queueLaunch -Algorithm SHA256).Hash.ToLowerInvariant()
$env:WINDOWS_WITNESS_QUEUE_SHA256 = $queueHash
$afterFxCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-r', $normalizedQueuePath)
@('@echo off', $afterFxCommandLine, 'exit /b %ERRORLEVEL%') | Set-Content -LiteralPath $launchWrapper -Encoding ASCII
$bootstrapText = @"
.effmach amd64
.expr /s masm
.echo WITNESS_CDB_BOOTSTRAP_ARMED
.echo WITNESS_CDB_AFTERFX_INITIAL_BREAK
qd
"@
$bootstrapText | Set-Content -LiteralPath $bootstrapCdbScript -Encoding ASCII
$launchArgumentValues = @('-pd', '-hd', '-logo', $bootstrapCdbTrace, '-cf', $bootstrapCdbScript, '--', $AfterFxPath, '-r', $normalizedQueuePath)
$launchArguments = Join-WindowsCommandLine $launchArgumentValues
$launch = Start-Process -FilePath $CdbPath -ArgumentList $launchArguments -RedirectStandardOutput $launchOut -RedirectStandardError $launchErr -NoNewWindow -PassThru
$launchStarted = $true
$deadline = (Get-Date).AddSeconds(60)
$desktopState = @()
while ((Get-Date) -lt $deadline) {
  $desktopState = @(Get-AfterFxState)
  if ($desktopState.Count -eq 1) { break }
  Start-Sleep -Milliseconds 250
}
if ($desktopState.Count -ne 1) {
  Finish (Failure 'cdb_launch' 'CDB-launched After Effects instance did not become uniquely observable' @('one_desktop_AfterFX_process', 'cdb_bootstrap') "matches=$($desktopState.Count)") 2
}
$bootstrapAePid = [int]$desktopState[0].pid
$observedCommandLine = [string]$desktopState[0].command_line
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline) {
  $launch.Refresh()
  if ($launch.HasExited) { break }
  Start-Sleep -Milliseconds 250
}
if (!$launch.HasExited) {
  Finish (Failure 'cdb_launch' 'CDB bootstrap did not detach from the launched After Effects process' @('cdb_bootstrap_exit') '') 2
}
$bootstrapTraceText = $(if (Test-Path -LiteralPath $bootstrapCdbTrace -PathType Leaf) { Get-Content -LiteralPath $bootstrapCdbTrace -Raw } else { '' })
$bootstrapObservedMarker = $bootstrapTraceText -match 'WITNESS_CDB_AFTERFX_INITIAL_BREAK'
if ($bootstrapTraceText -notmatch 'WITNESS_CDB_BOOTSTRAP_ARMED' -or !$bootstrapObservedMarker) {
  Finish (Failure 'cdb_bootstrap' 'CDB did not reach the directly launched AfterFX.exe initial breakpoint' @('WITNESS_CDB_BOOTSTRAP_ARMED', 'WITNESS_CDB_AFTERFX_INITIAL_BREAK') $bootstrapTraceText) 2
}
$deadline = (Get-Date).AddSeconds(60)
while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $queueBootstrap -PathType Leaf)) { Start-Sleep -Milliseconds 250 }
if (!(Test-Path -LiteralPath $queueBootstrap -PathType Leaf)) {
  Finish (Failure 'jsx_launch' 'CDB-launched After Effects process did not execute the queue JSX' @('queue_bootstrap.log') '') 2
}
$queueBootstrapObserved = $true
try { $queueBootstrapBinding = Read-QueueBootstrapBinding $queueBootstrap }
catch { Finish (Failure 'queue_binding' $_.Exception.Message @('queue_bootstrap_binding') '') 2 }
foreach ($field in @('run_id', 'work', 'root', 'queue_sha256')) {
  if ($null -eq $queueBootstrapBinding.$field) {
    Finish (Failure 'queue_binding' "queue bootstrap marker is missing $field" @("queue_bootstrap:$field") '') 2
  }
}
if ([string]$queueBootstrapBinding.run_id -cne $runId -or
    ![string]::Equals([string]$queueBootstrapBinding.work, $work, [StringComparison]::OrdinalIgnoreCase) -or
    ![string]::Equals([string]$queueBootstrapBinding.root, $PackageRoot, [StringComparison]::OrdinalIgnoreCase) -or
    [string]$queueBootstrapBinding.queue_sha256 -cne $queueHash) {
  Finish (Failure 'queue_binding' 'queue bootstrap marker does not match this run/package/script' @('queue_bootstrap:run_id', 'queue_bootstrap:work', 'queue_bootstrap:root', 'queue_bootstrap:queue_sha256') ($queueBootstrapBinding | ConvertTo-Json -Compress)) 2
}
$postBootstrapState = @(Get-AfterFxState)
if ($postBootstrapState.Count -ne 1 -or [int]$postBootstrapState[0].pid -ne $bootstrapAePid) {
  Finish (Failure 'queue_binding' 'queue bootstrap marker is not bound to the launched After Effects process' @('same_afterfx_pid', 'same_afterfx_session', 'same_afterfx_path') "launched_pid=$bootstrapAePid matches=$($postBootstrapState.Count)") 2
}
$boundPid = $bootstrapAePid

foreach ($case in @($contract.cases | Sort-Object order)) {
  $caseId = [string]$case.id
  $ready = Join-Path $work ("ready_$caseId.marker")
  $continue = Join-Path $work ("continue_$caseId.marker")
  $result = Join-Path $work ("ae_result_$caseId.json")
  $trace = Join-Path $work ("cdb_trace_$caseId.txt")
  $stdout = Join-Path $work ("cdb_stdout_$caseId.txt")
  $stderr = Join-Path $work ("cdb_stderr_$caseId.txt")
  $script = Join-Path $work ("probe_$caseId.cdb")
  $caseToken = '{0:D3}' -f ([int]$case.order)
  $shortTrace = Join-Path $launchDir ("c_$caseToken.log")
  $shortScript = Join-Path $launchDir ("c_$caseToken.cdb")
  $activeCdbTrace = $shortTrace
  $activeCdbTraceEvidence = $trace

  $deadline = (Get-Date).AddSeconds(180)
  while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $ready)) { Start-Sleep -Milliseconds 250 }
  if (!(Test-Path -LiteralPath $ready -PathType Leaf)) { Finish (Failure 'readiness' "ready marker missing for $caseId" @("ready_$caseId.marker") '') 2 }
  $readyText = Get-Content -LiteralPath $ready -Raw
  if ($readyText -notmatch ('case_id=' + [regex]::Escape($caseId)) -or $readyText -notmatch 'effect_loaded=1' -or $readyText -notmatch 'parameters_applied=1') {
    Finish (Failure 'readiness' "marker is not render-ready for $caseId" @('case_id', 'effect_loaded=1', 'parameters_applied=1') $readyText) 2
  }

  $loaded = @()
  $deadline = (Get-Date).AddSeconds(30)
  while ((Get-Date) -lt $deadline -and $loaded.Count -ne 1) {
    $loaded = @(Get-AfterFxState | ForEach-Object {
      $process = Get-Process -Id $_.pid -ErrorAction SilentlyContinue
      try {
        $module = $process.Modules | Where-Object { $_.FileName -ieq $AexPath } | Select-Object -First 1
        if ($module) { [pscustomobject]@{Process=$process; Module=$module} }
      } catch {}
    })
    if ($loaded.Count -ne 1) { Start-Sleep -Milliseconds 250 }
  }
  if ($loaded.Count -ne 1) { Finish (Failure 'desktop_process_discovery' "exactly one loaded module was not found for $caseId" @('actual_ae_process_module') "matches=$($loaded.Count)") 2 }
  $ae = $loaded[0].Process
  $module = $loaded[0].Module
  $loadedHash = (Get-FileHash -LiteralPath $module.FileName -Algorithm SHA256).Hash.ToLowerInvariant()
  $base = '0x{0:x}' -f $module.BaseAddress.ToInt64()
  if ($loadedHash -ne $hash) { Finish (Failure 'module_hash' 'loaded module hash mismatch' @('loaded_aex_sha256') "actual=$loadedHash") 2 }
  if ([int]$ae.Id -ne $boundPid) {
    Finish (Failure 'same_run_identity' 'AE PID changed after queue bootstrap' @('shared_ae_pid') "pid=$($ae.Id) expected=$boundPid") 2
  }
  if ($null -eq $boundBase) { $boundBase = $base }
  elseif ($base -ne $boundBase) {
    Finish (Failure 'same_run_identity' 'AE PID or module base changed between cases' @('shared_ae_pid', 'shared_module_base') "pid=$($ae.Id) base=$base") 2
  }

  try {
    Render-Cdb $case $shortTrace $module.BaseAddress.ToInt64() $hash | Set-Content -LiteralPath $shortScript -Encoding ASCII
    Copy-Item -LiteralPath $shortScript -Destination $script -Force
  }
  catch { Finish (Failure 'cdb_template' $_.Exception.Message @('resolved_cdb_template') '') 2 }
  $cdbArguments = Join-WindowsCommandLine @('-cf', $shortScript, '-p', [string]$boundPid)
  $cdb = Start-Process -FilePath $CdbPath -ArgumentList $cdbArguments -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru
  $deadline = (Get-Date).AddSeconds([int]$contract.cdb.arm_timeout_seconds)
  while ((Get-Date) -lt $deadline) {
    if ((Test-Path -LiteralPath $shortTrace) -and (Get-Content -LiteralPath $shortTrace -Raw) -match [regex]::Escape([string]$contract.cdb.armed_marker)) { break }
    $cdb.Refresh(); if ($cdb.HasExited) { break }; Start-Sleep -Milliseconds 250
  }
  if (!(Test-Path -LiteralPath $shortTrace) -or (Get-Content -LiteralPath $shortTrace -Raw) -notmatch [regex]::Escape([string]$contract.cdb.armed_marker)) {
    Finish (Failure 'cdb_arm' "CDB did not arm for $caseId" @([string]$contract.cdb.armed_marker) '') 2
  }
  Set-Content -LiteralPath $continue -Value 'continue' -Encoding ASCII
  $deadline = (Get-Date).AddSeconds([int]$contract.cdb.capture_timeout_seconds)
  while ((Get-Date) -lt $deadline -and !$cdb.HasExited) { Start-Sleep -Milliseconds 250; $cdb.Refresh() }
  if (!$cdb.HasExited) { Finish (Failure 'cdb_capture' "CDB did not complete for $caseId" @('cdb_exit') '') 2 }
  if (Test-Path -LiteralPath $shortTrace) {
    Copy-Item -LiteralPath $shortTrace -Destination $trace -Force
    Get-Content -LiteralPath $shortTrace | Add-Content -LiteralPath $combinedTrace
  }

  $deadline = (Get-Date).AddSeconds(180)
  while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $result)) { Start-Sleep -Milliseconds 250 }
  if (!(Test-Path -LiteralPath $result -PathType Leaf)) { Finish (Failure 'render_result' "AE result missing for $caseId" @("ae_result_$caseId.json") '') 2 }
  $aeResult = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json
  if ($aeResult.status -ne 'ok' -or [int]$aeResult.project_bits_per_channel -ne [int]$contract.project.bits_per_channel) {
    Finish (Failure 'render_result' "AE render result is invalid for $caseId" @('status=ok', 'project_bits_per_channel') ($aeResult | ConvertTo-Json -Compress)) 2
  }
}

$identity = [ordered]@{run_id=$runId; ae_pid=$boundPid; module_base=$boundBase}
$identity | ConvertTo-Json | Set-Content -LiteralPath $identityPath -Encoding UTF8
& py -3 $runtimePath validate --contract $contractPath --trace $combinedTrace --identity $identityPath --output $statusPath
$validateCode = $LASTEXITCODE
if (!(Test-Path -LiteralPath $statusPath -PathType Leaf)) { Finish (Failure 'trace_validation' 'validator did not produce status JSON' @('validation_status.json') '') 2 }
$validated = Get-Content -LiteralPath $statusPath -Raw | ConvertFrom-Json
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
