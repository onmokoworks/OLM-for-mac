param(
  [string]$PackageRoot = '',
  [string]$WorkRoot = "$env:TEMP\olmsmoother2_case0012_live_config_binding_20260713",
  [string]$AfterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$Cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
)

$ErrorActionPreference = 'Stop'
if (-not $PackageRoot) { $PackageRoot = Split-Path -Parent $PSCommandPath }
$caseRoot = Join-Path $PackageRoot 'case'
$jsx = Join-Path $caseRoot 'ae_render_single_case.jsx'
$requestDir = $caseRoot
$work = Join-Path $WorkRoot 'single_fresh_run'
$returnJson = Join-Path $work 'RETURN.json'
$stdout = Join-Path $work 'cdb_stdout.txt'
$stderr = Join-Path $work 'cdb_stderr.txt'
$cdbTemplate = Join-Path $PackageRoot 'case0012_live_config_binding.cdb.in'
$cdbScript = Join-Path $work 'case0012_live_config_binding.cdb'
$expectedAexSha256 = '7d42c00fe382304ea8a2b9d72af4f3a55f18b6fc03f6174786c97d7618b744c7'
$expectedAexSize = 192000L
$aexPath = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMSmoother2.aex'
foreach ($path in @($AfterFx, $Cdb, $jsx, $cdbTemplate, (Join-Path $requestDir 'request_manifest.json'), (Join-Path $requestDir 'reference_manifest.json'), (Join-Path $requestDir 'input\case_0012_before_effects.png'))) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing packaged runner asset or tool: $path" }
}
if (-not (Test-Path -LiteralPath $aexPath -PathType Leaf)) { throw "Pinned AEX missing: $aexPath" }
$aex = Get-Item -LiteralPath $aexPath
$aexSha256 = (Get-FileHash -LiteralPath $aexPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($aex.Length -ne $expectedAexSize -or $aexSha256 -ne $expectedAexSha256) {
  throw "Pinned AEX identity mismatch: size=$($aex.Length) sha256=$aexSha256"
}
New-Item -ItemType Directory -Force -Path $work | Out-Null
$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = 'legacy_case_0012_gamma5_red_blue_current_aex'
$env:OLM_AE_OUTPUT_DIR = $work
$env:OLM_AE_LOG_PATH = (Join-Path $work 'AE_SINGLE_CASE.log')
$env:OLM_AE_RESULT_JSON = (Join-Path $work 'AE_SINGLE_CASE_RESULT.json')
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{}'
$env:OLM_AE_FORCE_NEW_PROJECT = '1'
$env:OLM_AE_FORCE_SOFTWARE = '1'
$env:OLM_AE_KEEP_OPEN = '0'
$runId = 's2cfg_' + (Get-Date -Format 'yyyyMMddHHmmssfff')
$template = Get-Content -LiteralPath $cdbTemplate -Raw
$template = $template.Replace('WORKDIR', $work).Replace('RUN_ID', $runId)
$template | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$cdbArgs = '-cf "' + $cdbScript + '" "' + $AfterFx + '" -r "' + $jsx + '"'
$proc = Start-Process -FilePath $Cdb -ArgumentList $cdbArgs -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru -Wait
$lines = @()
if (Test-Path $stdout) { $lines += Get-Content $stdout }
if (Test-Path $stderr) { $lines += Get-Content $stderr }
$lines = @($lines | ForEach-Object { [string]$_ })
$lines | Set-Content (Join-Path $work 'cdb_console.txt') -Encoding UTF8

function Field([string]$line, [string]$key) {
  $m = [regex]::Match($line, "(?:^|\s)$key=([^\s]+)")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function Vec([string]$line, [string]$key) {
  $raw = Field $line $key
  if ($null -eq $raw) { return $null }
  return @($raw.Split(','))
}

function Marker([string]$prefix) {
  return ($lines | Where-Object { $_ -match "^$prefix\s" } | Select-Object -Last 1)
}

function DecodeModeName($modeByte) {
  switch ($modeByte) {
    '0' { return 'no_gamma' }
    '1' { return 'gamma_all_channels' }
    '3' { return 'gamma_colors' }
    default { return "mode_$modeByte" }
  }
}

$start = Marker 'S2_CFG_RUN_START'
$bind = Marker 'S2_CFG_BIND'
$c280 = Marker 'S2_CFG_C280'
$cce0 = Marker 'S2_CFG_CCE0'
$writer = Marker 'S2_CFG_WRITER'
$missing = @()
foreach ($pair in @(@('run_start',$start), @('bind',$bind), @('c280',$c280), @('cce0',$cce0), @('writer',$writer))) {
  if (-not $pair[1]) { $missing += $pair[0] }
}
if (-not ($start -and (Field $start 'case_id') -eq 'legacy_case_0012_gamma5_red_blue_current_aex' -and (Field $start 'x') -eq '91' -and (Field $start 'y') -eq '841' -and (Field $start 'idx') -eq '105' -and (Field $start 'descriptor') -eq '91,841,1,91,843,5')) {
  $missing += 'witness_identity'
}
$runIds = @($lines | ForEach-Object { if ($_ -match '^S2_CFG_\S+.*\brun_id=([^\s]+)') { $Matches[1] } } | Sort-Object -Unique)
if ($runIds.Count -ne 1) { $missing += 'same_run_identity' }
$requiredValues = @(
  @($bind, 'module'),
  @($bind, 'module_base'),
  @($bind, 'writer_hook'),
  @($bind, 'c280_hook'),
  @($bind, 'cce0_hook'),
  @($bind, 'binding_expression'),
  @($bind, 'pointer_context'),
  @($c280, 'config_pointer'),
  @($c280, 'config_pointer_arithmetic'),
  @($c280, 'config_raw_bytes'),
  @($c280, 'scale_fixed'),
  @($cce0, 'config_pointer'),
  @($cce0, 'config_pointer_arithmetic'),
  @($cce0, 'config_raw_bytes'),
  @($cce0, 'mode_byte'),
  @($writer, 'writer_site'),
  @($writer, 'writer_rgba_u8'),
  @($writer, 'writer_rgba_float')
)
foreach ($pair in $requiredValues) {
  if (-not (Field $pair[0] $pair[1])) { $missing += $pair[1] }
}
$c280Bytes = if ($c280) { Vec $c280 'config_raw_bytes' } else { $null }
$cce0Bytes = if ($cce0) { Vec $cce0 'config_raw_bytes' } else { $null }
if ($c280Bytes -and $c280Bytes.Count -ne 8) { $missing += 'c280_raw_span' }
if ($cce0Bytes -and $cce0Bytes.Count -ne 7) { $missing += 'cce0_raw_span' }
$status = if ($missing.Count -eq 0) { 'answered' } else { 'exact_bind_failure' }
$modeByte = if ($cce0) { Field $cce0 'mode_byte' } else { $null }
$modeName = if ($modeByte) { DecodeModeName $modeByte } else { $null }
$result = @{
  schema = 'olmsmoother2_case0012_live_config_binding_return_v1'
  request_id = 'olmsmoother2_case0012_live_config_binding_20260713'
  status = $status
  run = @{
    run_id = if ($runIds.Count -ge 1) { $runIds[0] } else { $null }
    case_id = 'legacy_case_0012_gamma5_red_blue_current_aex'
    pixel = @(91, 841)
    module = if ($bind) { Field $bind 'module' } else { $null }
    module_base = if ($bind) { Field $bind 'module_base' } else { $null }
  }
  bind = @{
    writer_hook = if ($bind) { Field $bind 'writer_hook' } else { $null }
    c280_hook = if ($bind) { Field $bind 'c280_hook' } else { $null }
    cce0_hook = if ($bind) { Field $bind 'cce0_hook' } else { $null }
    binding_expression = if ($bind) { Field $bind 'binding_expression' } else { $null }
    pointer_context = if ($bind) { Field $bind 'pointer_context' } else { $null }
  }
  observations = @{
    idx = 105
    descriptor = @(91, 841, 1, 91, 843, 5)
    c280 = @{
      config_pointer = if ($c280) { Field $c280 'config_pointer' } else { $null }
      config_pointer_arithmetic = if ($c280) { Field $c280 'config_pointer_arithmetic' } else { $null }
      config_raw_bytes = $c280Bytes
      scale_fixed = if ($c280) { Vec $c280 'scale_fixed' } else { $null }
    }
    cce0 = @{
      config_pointer = if ($cce0) { Field $cce0 'config_pointer' } else { $null }
      config_pointer_arithmetic = if ($cce0) { Field $cce0 'config_pointer_arithmetic' } else { $null }
      config_raw_bytes = $cce0Bytes
      mode_byte = $modeByte
      mode_name = $modeName
    }
    final_writer = @{
      site = if ($writer) { Field $writer 'writer_site' } else { $null }
      rgba_u8 = if ($writer) { Vec $writer 'writer_rgba_u8' } else { $null }
      rgba_float = if ($writer) { Vec $writer 'writer_rgba_float' } else { $null }
    }
  }
  failure = @{
    stage = if ($missing -contains 'run_start') { 'run_start' } elseif ($missing -contains 'bind') { 'bind' } else { 'typed_read' }
    reason = if ($missing.Count) { 'Missing decoded config-binding fields: ' + ($missing -join ', ') } else { $null }
    module = if ($bind) { Field $bind 'module' } else { $null }
    hook = if ($bind) { Field $bind 'c280_hook' } else { $null }
    run_id = if ($runIds.Count -ge 1) { $runIds[0] } else { $null }
    case_id = 'legacy_case_0012_gamma5_red_blue_current_aex'
    pixel = @(91, 841)
    pointer_context = if ($bind) { Field $bind 'pointer_context' } else { $null }
    last_observation = if ($writer) { 'final_writer' } elseif ($cce0) { 'cce0' } elseif ($c280) { 'c280' } elseif ($bind) { 'bind' } else { $null }
    missing = $missing
  }
}
$result | ConvertTo-Json -Depth 12 | Set-Content $returnJson -Encoding UTF8
if ($status -ne 'answered') { exit 2 }
exit 0
