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
$transportKind = if ($contract.transport -and $contract.transport.kind) { [string]$contract.transport.kind } else { 'cdb' }
if (!$CdbPath -and $transportKind -eq 'cdb') { $CdbPath = [string]$contract.host.cdb_path }
$runId = ([string]$contract.run_id_prefix) + '-' + ([guid]::NewGuid().ToString('N'))
$work = Join-Path $WorkRoot $runId
New-Item -ItemType Directory -Force -Path $work | Out-Null
$work = (Get-Item -LiteralPath $work).FullName
$combinedTrace = Join-Path $work 'combined_cdb_trace.txt'
$identityPath = Join-Path $work 'runtime_identity.json'
$statusPath = Join-Path $work 'validation_status.json'
$pluginCacheRescanPath = Join-Path $work 'plugin_cache_rescan.json'
$launchOut = Join-Path $work 'afterfx_launcher_stdout.txt'
$launchErr = Join-Path $work 'afterfx_launcher_stderr.txt'
$processDiagnostics = Join-Path $work 'afterfx_process_diagnostics.json'
$bootstrapCdbScriptEvidence = Join-Path $work 'afterfx_bootstrap.cdb'
$bootstrapCdbTraceEvidence = Join-Path $work 'afterfx_bootstrap_cdb_trace.txt'
$launchWrapperEvidence = Join-Path $work 'afterfx_launch_wrapper.cmd'
$dispatchWrapperEvidence = Join-Path $work 'afterfx_dispatch_wrapper.cmd'
$queueLaunchEvidence = Join-Path $work 'launched_queue.jsx'
$queuePath = Join-Path $PackageRoot ([string]$contract.queue).Replace('/', '\')
$sessionId = (Get-Process -Id $PID).SessionId
$launch = $null
$cdb = $null
$injectorProcess = $null
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
$dispatchWrapper = $null
$scheduledTaskName = $null
$scheduledTaskCreated = $false
$dispatchScheduledTaskName = $null
$dispatchScheduledTaskCreated = $false
$normalizedQueuePath = $null
$observedCommandLine = $null
$renderAePid = $null
$bootstrapObservedMarker = $false
$bootstrapPluginLoadClaimed = $false
$queueBootstrapObserved = $false
$queueBootstrapBinding = $null
$queueRetryProcesses = @()
$queueBindingAmbiguous = $false
$bootstrapAePid = $null
$activeCdbTrace = $null
$activeCdbTraceEvidence = $null
$captureDiagnostics = @()

function Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last, [object]$diagnostics = $null) {
  $body = [ordered]@{
    schema_version = 1
    status = 'exact_bind_failure'
    request_id = [string]$contract.request_id
    failure = [ordered]@{stage=$stage; reason=$reason; missing_fields=@($missing); last_observation=$last}
  }
  if ($null -ne $diagnostics) { $body.failure['capture_diagnostics'] = $diagnostics }
  return $body
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
      $_.ExecutablePath -and
      [IO.Path]::GetFullPath($_.ExecutablePath) -ieq $AfterFxPath
    } |
    ForEach-Object {
      [ordered]@{pid=[int]$_.ProcessId; parent_pid=[int]$_.ParentProcessId; session_id=[int]$_.SessionId; path=$_.ExecutablePath; command_line=$_.CommandLine}
    })
}

function Test-PluginCacheModuleMatch([string]$keyName, [string]$moduleFilename) {
  if ([string]::IsNullOrWhiteSpace($keyName) -or [string]::IsNullOrWhiteSpace($moduleFilename)) { return $false }
  $pattern = '^' + [regex]::Escape($moduleFilename) + '(?:_.+)?$'
  return $keyName -imatch $pattern
}

function Get-PluginCacheRoots {
  $roots = @()
  $afterEffectsRoot = 'HKCU:\Software\Adobe\After Effects'
  if (!(Test-Path -LiteralPath $afterEffectsRoot)) { return @() }
  foreach ($versionKey in @(Get-ChildItem -LiteralPath $afterEffectsRoot -ErrorAction SilentlyContinue)) {
    foreach ($cacheName in @('PluginCache', 'PluginCache.64', 'HeadlessPluginCache', 'HeadlessPluginCache.64')) {
      $candidate = Join-Path $versionKey.PSPath $cacheName
      if (Test-Path -LiteralPath $candidate) {
        $roots += Get-Item -LiteralPath $candidate
      }
    }
  }
  return @($roots | Sort-Object PSPath -Unique)
}

function Get-RegistryKeySnapshot([string]$path) {
  $item = Get-Item -LiteralPath $path
  $values = [ordered]@{}
  $properties = Get-ItemProperty -LiteralPath $path
  foreach ($property in $properties.PSObject.Properties) {
    if ($property.Name -like 'PS*') { continue }
    $values[$property.Name] = $property.Value
  }
  $children = @()
  foreach ($child in @(Get-ChildItem -LiteralPath $path -ErrorAction SilentlyContinue | Sort-Object Name)) {
    $children += (Get-RegistryKeySnapshot $child.PSPath)
  }
  return [ordered]@{
    path = $item.PSPath
    values = $values
    children = $children
  }
}

function Write-PluginCacheRescanReport([string]$path, [object]$report) {
  $report | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
}

function Invoke-PluginCacheRescan([object]$plugin, [string]$aexPath, [string]$reportPath) {
  $moduleFilename = [string]$plugin.module_filename
  $report = [ordered]@{
    enabled = [bool]$plugin.cache_rescan
    module_filename = $moduleFilename
    aex_path = $aexPath
    match_rule = 'registry leaf must equal module_filename or module_filename + underscore suffix'
    roots_scanned = @()
    matched_keys = @()
    deleted_keys = @()
  }
  if (-not $report.enabled) { return }
  try {
    $roots = @(Get-PluginCacheRoots)
    $report.roots_scanned = @($roots | ForEach-Object { $_.PSPath })
    $matches = @()
    foreach ($root in $roots) {
      foreach ($key in @(Get-ChildItem -LiteralPath $root.PSPath -Recurse -ErrorAction SilentlyContinue)) {
        if (Test-PluginCacheModuleMatch $key.PSChildName $moduleFilename) {
          $matches += $key
        }
      }
    }
    $uniqueMatches = @($matches | Sort-Object PSPath -Unique)
    foreach ($match in $uniqueMatches) {
      $report.matched_keys += (Get-RegistryKeySnapshot $match.PSPath)
    }
    foreach ($match in @($uniqueMatches | Sort-Object { $_.PSPath.Length } -Descending)) {
      Remove-Item -LiteralPath $match.PSPath -Recurse -Force
      $report.deleted_keys += $match.PSPath
    }
    Write-PluginCacheRescanReport $reportPath $report
  } catch {
    $report['error'] = $_.Exception.Message
    Write-PluginCacheRescanReport $reportPath $report
    throw
  }
}

function Stop-WitnessProcesses {
  foreach ($case in @($contract.cases)) {
    $ready = Join-Path $work ("ready_" + $case.id + '.marker')
    $continue = Join-Path $work ("continue_" + $case.id + '.marker')
    if ((Test-Path -LiteralPath $ready) -and !(Test-Path -LiteralPath $continue)) {
      Set-Content -LiteralPath $continue -Value 'abort' -Encoding ASCII -ErrorAction SilentlyContinue
    }
  }
  Stop-CdbCapture
  if ($injectorProcess -and !$injectorProcess.HasExited) { Stop-Process -Id $injectorProcess.Id -Force -ErrorAction SilentlyContinue }
  if ($launch -and !$launch.HasExited) { Stop-Process -Id $launch.Id -Force -ErrorAction SilentlyContinue }
  foreach ($retry in @($queueRetryProcesses)) {
    if ($retry -and !$retry.HasExited) { Stop-Process -Id $retry.Id -Force -ErrorAction SilentlyContinue }
  }
  if ($launchStarted) {
    foreach ($state in @(Get-AfterFxState)) {
      Stop-Process -Id $state.pid -Force -ErrorAction SilentlyContinue
      Wait-Process -Id $state.pid -Timeout 10 -ErrorAction SilentlyContinue
    }
  }
  if ($scheduledTaskCreated -and $scheduledTaskName) {
    & schtasks.exe /Delete /TN $scheduledTaskName /F *> $null
  }
  if ($dispatchScheduledTaskCreated -and $dispatchScheduledTaskName) {
    & schtasks.exe /Delete /TN $dispatchScheduledTaskName /F *> $null
  }
}

function Stop-CdbCapture {
  if ($cdb -and !$cdb.HasExited) {
    Stop-Process -Id $cdb.Id -Force -ErrorAction SilentlyContinue
  }
  if ($cdb) { Wait-Process -Id $cdb.Id -Timeout 10 -ErrorAction SilentlyContinue }
}

function Get-TypedHitCount([string]$path) {
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { return 0 }
  $prefixes = @($contract.validation.events | ForEach-Object { [string]$_.prefix })
  return @(
    Get-Content -LiteralPath $path -ErrorAction SilentlyContinue |
      Where-Object {
        $prefix = (([string]$_).TrimStart() -split '\s+', 2)[0]
        $prefixes -contains $prefix
      }
  ).Count
}

function New-CaptureDiagnostics([string]$caseId, [string]$tracePath, [bool]$timedOut) {
  $typedHitCount = Get-TypedHitCount $tracePath
  [ordered]@{
    case_id = $caseId
    typed_hit_count = [int]$typedHitCount
    no_hit_reason = $(if ($typedHitCount -eq 0) {
        if ($timedOut) { 'cdb_capture_timeout_without_typed_hit' } else { 'cdb_exited_without_typed_hit' }
      } else { $null })
    cdb_capture_timed_out = $timedOut
    cdb_cleanup = $(if ($timedOut) { 'terminated_after_capture_timeout' } else { 'detached_or_exited' })
  }
}

function Copy-WitnessLaunchEvidence {
  foreach ($pair in @(
    [pscustomobject]@{Source=$bootstrapCdbScript; Destination=$bootstrapCdbScriptEvidence}
    [pscustomobject]@{Source=$bootstrapCdbTrace; Destination=$bootstrapCdbTraceEvidence}
    [pscustomobject]@{Source=$launchWrapper; Destination=$launchWrapperEvidence}
    [pscustomobject]@{Source=$dispatchWrapper; Destination=$dispatchWrapperEvidence}
    [pscustomobject]@{Source=$queueLaunch; Destination=$queueLaunchEvidence}
    [pscustomobject]@{Source=$queueBootstrap; Destination=(Join-Path $work 'queue_bootstrap.log')}
    [pscustomobject]@{Source=$activeCdbTrace; Destination=$activeCdbTraceEvidence}
  )) {
    if ($pair.Source -and $pair.Destination -and (Test-Path -LiteralPath $pair.Source -PathType Leaf)) {
      Copy-Item -LiteralPath $pair.Source -Destination $pair.Destination -Force -ErrorAction SilentlyContinue
    }
  }
  # CDB artifacts such as .writemem outputs are written beside the short trace
  # path. Preserve them before the temporary Public\OLMWitness directory is
  # removed; the contract may refer to the corresponding work trace prefix.
  if ($activeCdbTrace -and $activeCdbTraceEvidence) {
    foreach ($artifact in @(Get-ChildItem -Path ($activeCdbTrace + '.*') -File -ErrorAction SilentlyContinue)) {
      $suffix = $artifact.FullName.Substring($activeCdbTrace.Length)
      Copy-Item -LiteralPath $artifact.FullName -Destination ($activeCdbTraceEvidence + $suffix) -Force -ErrorAction SilentlyContinue
    }
  }
}

function Finish([object]$body, [int]$code) {
  Stop-WitnessProcesses
  $captureDiagnostics | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $work 'capture_diagnostics.json') -Encoding UTF8 -ErrorAction SilentlyContinue
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
    queue_binding_ambiguous = [bool]$queueBindingAmbiguous
    session_id = [int]$sessionId
    observed_afterfx = @(Get-AfterFxState)
    cdb_alive_after_cleanup = [bool]($cdb -and !$cdb.HasExited)
  } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $processDiagnostics -Encoding UTF8 -ErrorAction SilentlyContinue
  Copy-WitnessLaunchEvidence
  $body | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statusPath -Encoding UTF8
  & py -3 $runtimePath bundle --contract $contractPath --status $statusPath --work $work
  $bundleCode = $LASTEXITCODE
  $returnJson = Join-Path $work ([string]$contract.return_bundle.json_name)
  $returnZip = Join-Path $work ([string]$contract.return_bundle.zip_name)
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
    CASE_ID=[string]$case.id; TRACE_PATH=$trace; ARTIFACT_PATH=$trace
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
  # CDB's `/t` suffixes the requested path with a timestamp. The runner watches
  # the exact path, so stale-trace protection comes from the fresh work dir.
  $text = $text.Replace('.logopen /t ', '.logopen ')
  if ($text -match '\{\{[^{}]+\}\}') { throw "unresolved CDB placeholder: $($Matches[0])" }
  return $text
}

function Render-CollectorConfig([object]$case, [string]$configPath, [string]$outputDir) {
  $templatePath = Join-Path $PackageRoot ([string]$contract.transport.package_config_template).Replace('/', '\')
  $text = Get-Content -LiteralPath $templatePath -Raw
  $fixed = [ordered]@{RUN_ID=$runId; AE_PID=[string]$boundPid; CASE_ID=[string]$case.id; OUTPUT_DIR=$outputDir.Replace('\', '/')}
  foreach ($pair in $fixed.GetEnumerator()) { $text = $text.Replace('{{' + $pair.Key + '}}', [string]$pair.Value) }
  foreach ($property in $case.template_values.psobject.Properties) {
    $text = $text.Replace('{{CASE_VALUE:' + $property.Name + '}}', [string]$property.Value)
  }
  if ($text -match '\{\{[^{}]+\}\}') { throw "unresolved collector config placeholder: $($Matches[0])" }
  $text | Set-Content -LiteralPath $configPath -Encoding UTF8
}

function Invoke-Collector([object]$case, [string]$outputDir, [string]$configPath, [string]$stdout, [string]$stderr) {
  $injectorPath = Join-Path $PackageRoot ([string]$contract.transport.package_injector_path).Replace('/', '\')
  $dllPath = Join-Path $PackageRoot ([string]$contract.transport.package_collector_dll).Replace('/', '\')
  $arguments = Join-WindowsCommandLine @('--pid', [string]$boundPid, '--dll', $dllPath, '--config', $configPath)
  $script:injectorProcess = Start-Process -FilePath $injectorPath -ArgumentList $arguments -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -Wait -PassThru
  $injectorExitCode = $injectorProcess.ExitCode
  if ($injectorExitCode -ne 0) {
    throw "collector injector failed for $($case.id) with exit code $injectorExitCode"
  }
}

function Read-CollectorStatus([string]$path, [string]$expectedStatus, [string]$caseId) {
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { return $null }
  try { $status = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
  catch {
    # The collector replaces this file atomically while publishing progress.
    # A reader can briefly race the replacement; retry until the enclosing
    # arm/capture deadline instead of turning a transient read into failure.
    return $null
  }
  if ($null -eq $status -or $status.status -ne $expectedStatus) { return $null }
  foreach ($field in @('run_id', 'ae_pid', 'case_id')) {
    if ($null -eq $status.$field) { throw "collector $expectedStatus status is missing $field for $caseId" }
  }
  if ([string]$status.run_id -cne $runId -or
      [string]$status.ae_pid -cne [string]$boundPid -or
      [string]$status.case_id -cne $caseId) {
    throw "collector $expectedStatus status identity mismatch for $caseId"
  }
  return $status
}

function Wait-CollectorStatus([string]$path, [string]$expectedStatus, [string]$caseId, [int]$timeoutSeconds) {
  $deadline = (Get-Date).AddSeconds($timeoutSeconds)
  while ((Get-Date) -lt $deadline) {
    $status = Read-CollectorStatus $path $expectedStatus $caseId
    if ($null -ne $status) { return $status }
    Start-Sleep -Milliseconds 250
  }
  throw "collector status=$expectedStatus was not observed for $caseId within ${timeoutSeconds}s"
}

function Validate-CollectorOutputs([object]$case, [string]$outputDir, [string]$combinedTrace, [object]$status) {
  if ($null -eq $status -or $status.status -ne 'ok') { throw "collector status is not ok for $($case.id)" }
  foreach ($relative in @($contract.transport.required_outputs)) {
    $path = Join-Path $outputDir ([string]$relative).Replace('/', '\')
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) { throw "collector output missing for $($case.id): $relative" }
    Copy-Item -LiteralPath $path -Destination (Join-Path $work ("collector_" + $case.id + '_' + [IO.Path]::GetFileName($path))) -Force
  }
  $tracePath = Join-Path $outputDir 'collector_trace.txt'
  Get-Content -LiteralPath $tracePath | Add-Content -LiteralPath $combinedTrace
}

foreach ($path in @($AexPath, $AfterFxPath, $(if ($transportKind -eq 'cdb') { $CdbPath } else { $null }), $queuePath)) {
  if (!$path) { continue }
  if (!(Test-Path -LiteralPath $path -PathType Leaf)) { Finish (Failure 'preflight' "required file missing: $path" @('preflight_file') '') 2 }
}
if (Get-Process -Name AfterFX -ErrorAction SilentlyContinue) {
  Finish (Failure 'desktop_launch' 'After Effects must be fully closed before this run' @('fresh_AfterFX_process') '') 2
}
$AexPath = (Get-Item -LiteralPath $AexPath).FullName
$AfterFxPath = (Get-Item -LiteralPath $AfterFxPath).FullName
if ($transportKind -eq 'cdb') { $CdbPath = (Get-Item -LiteralPath $CdbPath).FullName }
$PackageRoot = (Get-Item -LiteralPath $PackageRoot).FullName
$hash = (Get-FileHash -LiteralPath $AexPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne [string]$contract.plugin.aex_sha256) {
  Finish (Failure 'module_hash' 'AEX hash does not match the witness contract' @('expected_aex_sha256') "actual=$hash") 2
}
if ($contract.plugin.PSObject.Properties.Name -contains 'cache_rescan' -and [bool]$contract.plugin.cache_rescan) {
  try { Invoke-PluginCacheRescan $contract.plugin $AexPath $pluginCacheRescanPath }
  catch { Finish (Failure 'plugin_cache_rescan' $_.Exception.Message @('plugin_cache_rescan') '') 2 }
}

$env:WINDOWS_WITNESS_WORK_ROOT = $work
$env:WINDOWS_WITNESS_RUN_ID = $runId
$env:WINDOWS_WITNESS_PACKAGE_ROOT = $PackageRoot
$env:WINDOWS_WITNESS_REQUEST_ID = [string]$contract.request_id
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
$dispatchWrapper = Join-Path $launchDir 'dispatch.cmd'
Copy-Item -LiteralPath $queuePath -Destination $queueLaunch -Force
Remove-Item -LiteralPath $queueBootstrap -Force -ErrorAction SilentlyContinue
if ($queueLaunch -match '\s') { Finish (Failure 'path_preflight' 'short JSX launch path contains whitespace' @('no_space_queue_path') $queueLaunch) 2 }
$normalizedQueuePath = [IO.Path]::GetFullPath($queueLaunch)
$queueHash = (Get-FileHash -LiteralPath $queueLaunch -Algorithm SHA256).Hash.ToLowerInvariant()
$env:WINDOWS_WITNESS_QUEUE_SHA256 = $queueHash
$directQueueLaunch = ([string]$env:WINDOWS_WITNESS_DIRECT_R -eq '1') -or ($transportKind -eq 'in_process_collector')
$afterFxCommandLine = if ($directQueueLaunch) {
  # `-ro` is AE's re-entrant file-script form. It preserves the same process
  # while allowing the queue to evaluate its bundled renderer.
  Join-WindowsCommandLine @($AfterFxPath, '-ro', $normalizedQueuePath)
} else {
  # Launch one ordinary desktop instance. `-m` permits a second AE process,
  # which makes the later `-r` dispatch lose the launch wrapper environment.
  Join-WindowsCommandLine @($AfterFxPath)
}
$queueDispatchCommandLine = Join-WindowsCommandLine @($AfterFxPath, '-ro', $normalizedQueuePath)
$environmentLines = @(
  ('set "WINDOWS_WITNESS_WORK_ROOT=' + $work + '"'),
  ('set "WINDOWS_WITNESS_RUN_ID=' + $runId + '"'),
  ('set "WINDOWS_WITNESS_PACKAGE_ROOT=' + $PackageRoot + '"'),
  ('set "WINDOWS_WITNESS_REQUEST_ID=' + [string]$contract.request_id + '"'),
  ('set "WINDOWS_WITNESS_QUEUE_SHA256=' + $queueHash + '"'),
  'set "OLM_AE_PAUSE_BEFORE_RENDER=1"',
  'set "OLM_AE_PAUSE_TIMEOUT_SECONDS=300"',
  'set "OLM_AE_FORCE_SOFTWARE=1"'
)
foreach ($property in $contract.project.environment.psobject.Properties) {
  $environmentLines += ('set "' + $property.Name + '=' + [string]$property.Value + '"')
}
$wrapperLines = @('@echo off') + $environmentLines + @($afterFxCommandLine, 'exit /b %ERRORLEVEL%')
$wrapperLines | Set-Content -LiteralPath $launchWrapper -Encoding ASCII
$launchArgumentValues = @('/d', '/s', '/c', $launchWrapper)
$launchArguments = Join-WindowsCommandLine $launchArgumentValues
$scheduledTaskName = '\OLM_Witness_' + ($runId -replace '[^A-Za-z0-9_-]', '_')
$taskStart = (Get-Date).AddMinutes(1)
$taskDate = $taskStart.ToString('yyyy/MM/dd', [Globalization.CultureInfo]::InvariantCulture)
$taskTime = $taskStart.ToString('HH:mm', [Globalization.CultureInfo]::InvariantCulture)
$taskOutput = & schtasks.exe /Create /TN $scheduledTaskName /TR $launchWrapper /SC ONCE /SD $taskDate /ST $taskTime /IT /F 2>&1
if ($LASTEXITCODE -ne 0) {
  Finish (Failure 'interactive_task' 'Could not create the interactive Windows task for AfterFX' @('interactive_task_created') ([string]::Join("`n", @($taskOutput)))) 2
}
$scheduledTaskCreated = $true
$taskOutput = & schtasks.exe /Run /TN $scheduledTaskName 2>&1
if ($LASTEXITCODE -ne 0) {
  Finish (Failure 'interactive_task' 'Could not run the interactive Windows task for AfterFX' @('interactive_task_started') ([string]::Join("`n", @($taskOutput)))) 2
}
$launchStarted = $true
$deadline = (Get-Date).AddSeconds(180)
$launchStates = @()
while ((Get-Date) -lt $deadline) {
  $launchStates = @(Get-AfterFxState)
  if ($launchStates.Count -eq 1) { break }
  if ($launchStates.Count -gt 1) {
    Finish (Failure 'desktop_process_discovery' 'After Effects launch produced more than one candidate process before queue dispatch' @('one_desktop_AfterFX_process') ($launchStates | ConvertTo-Json -Compress)) 2
  }
  Start-Sleep -Milliseconds 250
}
if ($launchStates.Count -ne 1) {
  Finish (Failure 'desktop_process_discovery' 'After Effects desktop process did not become observable' @('one_desktop_AfterFX_process') '') 2
}
$launch = Get-Process -Id ([int]$launchStates[0].pid) -ErrorAction SilentlyContinue
if (!$launch) {
  Finish (Failure 'desktop_process_discovery' 'After Effects process disappeared before queue dispatch' @('stable_AfterFX_process') '') 2
}
$mainAePid = [int]$launch.Id
$dispatchTaskOutput = @()
if (!$directQueueLaunch) {
  # AE 2025 may execute `-r` in a second desktop process. Give that process
  # the same run identity as the warm-up process so the JSX can bind itself.
  $dispatchLines = @('@echo off') + $environmentLines + @($queueDispatchCommandLine, 'exit /b %ERRORLEVEL%')
  $dispatchLines | Set-Content -LiteralPath $dispatchWrapper -Encoding ASCII
  $dispatchScheduledTaskName = '\OLM_Witness_Dispatch_' + ($runId -replace '[^A-Za-z0-9_-]', '_')
  $dispatchTaskOutput = & schtasks.exe /Create /TN $dispatchScheduledTaskName /TR $dispatchWrapper /SC ONCE /SD $taskDate /ST $taskTime /IT /F 2>&1
  if ($LASTEXITCODE -ne 0) {
    Finish (Failure 'jsx_dispatch' 'Could not create the interactive queue dispatch task' @('queue_dispatch_task_created') ([string]::Join("`n", @($dispatchTaskOutput)))) 2
  }
  $dispatchScheduledTaskCreated = $true
  $dispatchTaskOutput = & schtasks.exe /Run /TN $dispatchScheduledTaskName 2>&1
  if ($LASTEXITCODE -ne 0) {
    Finish (Failure 'jsx_dispatch' 'Could not run the interactive queue dispatch task' @('queue_dispatch_task_started') ([string]::Join("`n", @($dispatchTaskOutput)))) 2
  }
}
$postDispatchStates = @(Get-AfterFxState)
if (!(@($postDispatchStates | Where-Object { [int]$_.pid -eq $mainAePid }).Count -eq 1)) {
  Finish (Failure 'same_run_identity' 'The original After Effects process disappeared during queue dispatch' @('shared_ae_pid') ($postDispatchStates | ConvertTo-Json -Compress)) 2
}
$deadline = (Get-Date).AddSeconds(180)
while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $queueBootstrap -PathType Leaf)) { Start-Sleep -Milliseconds 250 }
if (!(Test-Path -LiteralPath $queueBootstrap -PathType Leaf)) {
  Finish (Failure 'jsx_launch' 'After Effects process did not execute the dispatched queue JSX' @('queue_bootstrap.log') ($postDispatchStates | ConvertTo-Json -Compress)) 2
}
$queueBootstrapObserved = $true
try { $queueBootstrapBinding = Read-QueueBootstrapBinding $queueBootstrap }
catch { Finish (Failure 'queue_binding' $_.Exception.Message @('queue_bootstrap_binding') '') 2 }
foreach ($field in @('run_id', 'work', 'root', 'request_id', 'queue_sha256')) {
  if ($null -eq $queueBootstrapBinding.$field) {
    Finish (Failure 'queue_binding' "queue bootstrap marker is missing $field" @("queue_bootstrap:$field") '') 2
  }
}
if ([string]$queueBootstrapBinding.run_id -cne $runId -or
    ![string]::Equals([string]$queueBootstrapBinding.work, $work, [StringComparison]::OrdinalIgnoreCase) -or
    ![string]::Equals([string]$queueBootstrapBinding.root, $PackageRoot, [StringComparison]::OrdinalIgnoreCase) -or
    [string]$queueBootstrapBinding.request_id -cne [string]$contract.request_id -or
    [string]$queueBootstrapBinding.queue_sha256 -cne $queueHash) {
  Finish (Failure 'queue_binding' 'queue bootstrap marker does not match this run/package/request/script' @('queue_bootstrap:run_id', 'queue_bootstrap:work', 'queue_bootstrap:root', 'queue_bootstrap:request_id', 'queue_bootstrap:queue_sha256') ($queueBootstrapBinding | ConvertTo-Json -Compress)) 2
}
$renderAePid = $mainAePid
if (!$directQueueLaunch) {
  $queueStates = @(Get-AfterFxState | Where-Object { [int]$_.pid -ne $mainAePid })
  if ($queueStates.Count -gt 1) {
    Finish (Failure 'queue_process_binding' 'More than one AE process remained after the JSX dispatch' @('zero_or_one_queue_AfterFX_process') ($queueStates | ConvertTo-Json -Compress)) 2
  }
  if ($queueStates.Count -eq 1) {
    $renderAePid = [int]$queueStates[0].pid
  }
}
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
    $loaded = @(Get-AfterFxState | Where-Object { [int]$_.pid -eq $renderAePid } | ForEach-Object {
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
  if ($null -eq $boundPid) { $boundPid = [int]$ae.Id }
  elseif ([int]$ae.Id -ne $boundPid) {
    Finish (Failure 'same_run_identity' 'AE PID changed after queue bootstrap' @('shared_ae_pid') "pid=$($ae.Id) expected=$boundPid") 2
  }
  if ($null -eq $boundBase) { $boundBase = $base }
  elseif ($base -ne $boundBase) {
    Finish (Failure 'same_run_identity' 'AE PID or module base changed between cases' @('shared_ae_pid', 'shared_module_base') "pid=$($ae.Id) base=$base") 2
  }

  if ($transportKind -eq 'cdb') {
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
  if (!$cdb.HasExited) {
    $capture = New-CaptureDiagnostics $caseId $shortTrace $true
    $captureDiagnostics += $capture
    Stop-CdbCapture
    Finish (Failure 'cdb_capture' "CDB did not complete for $caseId; CDB was terminated and AfterFX was stopped" @('cdb_exit') ("typed_hit_count=" + $capture.typed_hit_count) $capture) 2
  }
  $captureDiagnostics += (New-CaptureDiagnostics $caseId $shortTrace $false)
  if (Test-Path -LiteralPath $shortTrace) {
    Copy-Item -LiteralPath $shortTrace -Destination $trace -Force
    Get-Content -LiteralPath $shortTrace | Add-Content -LiteralPath $combinedTrace
  }
  } else {
    $collectorOutputDir = Join-Path $work ("exports\" + $caseId)
    New-Item -ItemType Directory -Force -Path $collectorOutputDir | Out-Null
    $collectorConfig = Join-Path $work ("collector_config_" + $caseId + '.json')
    $collectorStdout = Join-Path $work ("collector_stdout_" + $caseId + '.txt')
    $collectorStderr = Join-Path $work ("collector_stderr_" + $caseId + '.txt')
    $collectorStatusPath = Join-Path $collectorOutputDir 'collector_status.json'
    foreach ($relative in @($contract.transport.required_outputs)) {
      Remove-Item -LiteralPath (Join-Path $collectorOutputDir ([string]$relative).Replace('/', '\')) -Force -ErrorAction SilentlyContinue
    }
    try {
      Render-CollectorConfig $case $collectorConfig $collectorOutputDir
      Invoke-Collector $case $collectorOutputDir $collectorConfig $collectorStdout $collectorStderr
      Wait-CollectorStatus $collectorStatusPath 'armed' $caseId ([int]$contract.transport.arm_timeout_seconds) | Out-Null
      Set-Content -LiteralPath $continue -Value 'continue' -Encoding ASCII
      $collectorCaptureDeadline = (Get-Date).AddSeconds([int]$contract.transport.capture_timeout_seconds)
      $collectorStatus = $null
      $aeResult = $null
      while ((Get-Date) -lt $collectorCaptureDeadline -and ($null -eq $collectorStatus -or $null -eq $aeResult)) {
        if ($null -eq $aeResult -and (Test-Path -LiteralPath $result -PathType Leaf)) {
          try { $aeResult = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json }
          catch { throw "AE result is not valid JSON for $caseId" }
        }
        if ($null -eq $collectorStatus) {
          $collectorStatus = Read-CollectorStatus $collectorStatusPath 'ok' $caseId
        }
        if ($null -eq $collectorStatus -or $null -eq $aeResult) { Start-Sleep -Milliseconds 250 }
      }
      if ($null -eq $aeResult) { throw "AE result missing for $caseId before collector capture completed" }
      if ($null -eq $collectorStatus) { throw "collector status=ok missing for $caseId before capture timeout" }
      Validate-CollectorOutputs $case $collectorOutputDir $combinedTrace $collectorStatus
    }
    catch { Finish (Failure 'collector_capture' $_.Exception.Message @('collector_injection_and_outputs') '') 2 }
  }

  if ($transportKind -eq 'cdb') {
    $deadline = (Get-Date).AddSeconds(180)
    while ((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $result)) { Start-Sleep -Milliseconds 250 }
    if (!(Test-Path -LiteralPath $result -PathType Leaf)) { Finish (Failure 'render_result' "AE result missing for $caseId" @("ae_result_$caseId.json") '') 2 }
    try { $aeResult = Get-Content -LiteralPath $result -Raw | ConvertFrom-Json }
    catch { Finish (Failure 'render_result' "AE result is not valid JSON for $caseId" @('valid_ae_result_json') '') 2 }
  }
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
if ($validated -is [pscustomobject]) {
  $validated | Add-Member -NotePropertyName capture_diagnostics -NotePropertyValue @($captureDiagnostics) -Force
}
Finish $validated $(if ($validateCode -eq 0 -and $validated.status -eq 'answered') { 0 } else { 2 })
