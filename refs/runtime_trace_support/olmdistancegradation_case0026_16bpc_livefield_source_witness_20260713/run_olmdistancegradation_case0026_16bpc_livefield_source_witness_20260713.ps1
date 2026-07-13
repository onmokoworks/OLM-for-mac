param(
  [string]$PackageRoot = '',
  [string]$WorkRoot = "$env:TEMP\olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713",
  [string]$AfterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$Cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe',
  [string]$PowerShell51 = 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe',
  [switch]$SkipPowerShell51Relay,
  [switch]$ParseOnly,
  [string]$TracePath = ''
)

$ErrorActionPreference = 'Stop'
$RequestId = 'olmdistancegradation_case0026_16bpc_livefield_source_witness_20260713'
$ExpectedAexSha256 = 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
$ExpectedAexSize = 26289664L
$ExpectedPoints = @('907:222,395:477,1589:579,898:670'.Split(','))
$ExpectedCaseId = 'case_0026'
$ExpectedCaseFullId = 'olmdistancegradation_extended__case_0026'
$Runner = Join-Path (if($PackageRoot){$PackageRoot}else{Split-Path -Parent $PSCommandPath}) 'case\ae_render_single_case.jsx'

function Field([string]$line, [string]$key) {
  $m = [regex]::Match($line, "(?:^|\s)$key=([^\s]+)")
  if ($m.Success) { return $m.Groups[1].Value }
  return $null
}

function VecInt([string]$line, [string]$key) {
  $raw = Field $line $key
  if ($null -eq $raw) { return $null }
  return @($raw.Split(',') | ForEach-Object { [int]$_ })
}

function Marker([string[]]$lines, [string]$prefix) {
  return @($lines | Where-Object { $_ -match "^$prefix\s" })
}

function New-Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last, [string]$runId='') {
  return [ordered]@{
    schema = 'olmdistancegradation_case0026_16bpc_livefield_source_witness_return_v1'
    request_id = $RequestId
    status = 'exact_bind_failure'
    run = [ordered]@{
      run_id = if($runId){$runId}else{$null}
      case_id = $ExpectedCaseFullId
      renderer = 'software'
      bits_per_channel = 16
      current_aex = [ordered]@{
        module = 'DistanceGradation.aex'
        path = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex'
        sha256 = 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
        size = 26289664
        module_base = $null
      }
    }
    points = @()
    failure = [ordered]@{
      stage = $stage
      reason = $reason
      run_id = if($runId){$runId}else{$null}
      case_id = $ExpectedCaseFullId
      missing = @($missing)
      last_observation = $last
    }
  }
}

function Convert-TraceToReturn([string]$path) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    return New-Failure 'trace' "missing trace: $path" @('trace') ''
  }
  $lines = @((Get-Content -LiteralPath $path) | ForEach-Object { [string]$_ })
  $records = @{}
  $lastObservation = $null
  foreach($line in $lines){
    if($line -match '^OLMDG_LFS_(ENTRY|FIELD|SOURCE|RETURN)\s'){
      $kind = $Matches[1]
      $caseId = Field $line 'case_id'
      $x = Field $line 'x'
      $y = Field $line 'y'
      if(-not $caseId -or -not $x -or -not $y){ continue }
      $key = "$caseId|$x|$y"
      if(-not $records.ContainsKey($key)){
        $records[$key] = [ordered]@{
          run_id = Field $line 'run_id'
          case_id = $caseId
          x = [int]$x
          y = [int]$y
        }
      }
      switch($kind){
        'ENTRY' {
          $records[$key]['module_base'] = Field $line 'module_base'
          $records[$key]['output_addr'] = Field $line 'output'
          $records[$key]['pre_output_words_agrb'] = VecInt $line 'pre_output_words_agrb'
          $records[$key]['in_out'] = [int](Field $line 'in_out')
          $records[$key]['inside_threshold'] = [int](Field $line 'inside_threshold')
          $records[$key]['outside_threshold'] = [int](Field $line 'outside_threshold')
          $records[$key]['use_bg'] = [int](Field $line 'use_bg')
          $records[$key]['invert'] = [int](Field $line 'invert')
          $records[$key]['render_mode'] = [int](Field $line 'render_mode')
          $records[$key]['interp_mode'] = [int](Field $line 'interp_mode')
          foreach($name in @('power_bits','grad_r_bits','grad_g_bits','grad_b_bits','bg_r_bits','bg_g_bits','bg_b_bits')){
            $records[$key][$name] = Field $line $name
          }
        }
        'FIELD' {
          $records[$key]['field_addr'] = Field $line 'rcx'
          $records[$key]['field_word_at_rcx_plus_2'] = [int](Field $line 'rcx_plus2_word')
          $records[$key]['field_raw_words_agrb'] = VecInt $line 'field_words_agrb'
          $records[$key]['field_base'] = Field $line 'field_base'
          $records[$key]['field_header'] = Field $line 'field_header'
          $records[$key]['field_rowbytes'] = [int](Field $line 'field_rowbytes')
          $records[$key]['field_pixel_size'] = [int](Field $line 'field_pixel_size')
        }
        'SOURCE' {
          $records[$key]['source_addr'] = Field $line 'rdx'
          $records[$key]['source_raw_words_agrb'] = VecInt $line 'source_words_agrb'
        }
        'RETURN' {
          $records[$key]['output_addr_after'] = Field $line 'output'
          $records[$key]['post_output_words_agrb'] = VecInt $line 'post_output_words_agrb'
        }
      }
      $lastObservation = $kind.ToLowerInvariant()
    }
  }

  $missing = @()
  $expectedKeys = @('case_0026|907|222','case_0026|395|477','case_0026|1589|579','case_0026|898|670')
  foreach($key in $expectedKeys){
    if(-not $records.ContainsKey($key)){ $missing += "missing:$key" }
  }
  $recordList = @($records.Values)
  $runIds = @($recordList | ForEach-Object { $_['run_id'] } | Where-Object { $_ } | Select-Object -Unique)
  if($recordList.Count -ne 4){ $missing += "record_count=$($recordList.Count)" }
  if($runIds.Count -ne 1){ $missing += 'same_run_identity' }
  foreach($record in $recordList){
    if($record['case_id'] -ne 'case_0026'){ $missing += "case_id:$($record['case_id'])" }
    $coord = "$($record['x']):$($record['y'])"
    if($ExpectedPoints -notcontains $coord){ $missing += "unexpected_xy:$coord" }
    foreach($fieldName in @(
      'module_base','output_addr','pre_output_words_agrb',
      'field_addr','field_word_at_rcx_plus_2','field_raw_words_agrb','field_base','field_header','field_rowbytes','field_pixel_size',
      'source_addr','source_raw_words_agrb','post_output_words_agrb',
      'power_bits','grad_r_bits','grad_g_bits','grad_b_bits','bg_r_bits','bg_g_bits','bg_b_bits'
    )){
      if(-not $record.ContainsKey($fieldName) -or $null -eq $record[$fieldName]){ $missing += "$coord:$fieldName" }
    }
    if(($record['pre_output_words_agrb'] -is [array]) -and $record['pre_output_words_agrb'].Count -ne 4){ $missing += "$coord:pre_output_words_agrb_span" }
    if(($record['field_raw_words_agrb'] -is [array]) -and $record['field_raw_words_agrb'].Count -ne 4){ $missing += "$coord:field_raw_words_agrb_span" }
    if(($record['source_raw_words_agrb'] -is [array]) -and $record['source_raw_words_agrb'].Count -ne 4){ $missing += "$coord:source_raw_words_agrb_span" }
    if(($record['post_output_words_agrb'] -is [array]) -and $record['post_output_words_agrb'].Count -ne 4){ $missing += "$coord:post_output_words_agrb_span" }
    if($record['in_out'] -ne 3 -or $record['inside_threshold'] -ne 158 -or $record['outside_threshold'] -ne 13 -or $record['use_bg'] -ne 1 -or $record['invert'] -ne 1 -or $record['render_mode'] -ne 1 -or $record['interp_mode'] -ne 4){ $missing += "$coord:case_tuple_ints" }
    if($record['power_bits'] -ne '0x40263bec' -or $record['grad_r_bits'] -ne '0x3de0e0ff' -or $record['grad_g_bits'] -ne '0x00000000' -or $record['grad_b_bits'] -ne '0x3f6eeeef' -or $record['bg_r_bits'] -ne '0x3f800000' -or $record['bg_g_bits'] -ne '0x00000000' -or $record['bg_b_bits'] -ne '0x00000000'){ $missing += "$coord:case_tuple_bits" }
  }
  if($missing.Count -gt 0){
    return New-Failure 'typed_capture' 'missing or mismatched live case0026 witness fields' $missing $lastObservation (if($runIds.Count -ge 1){$runIds[0]}else{''})
  }

  $points = @()
  foreach($xy in @(@(907,222),@(395,477),@(1589,579),@(898,670))){
    $key = "case_0026|$($xy[0])|$($xy[1])"
    $record = $records[$key]
    $points += [ordered]@{
      xy = @($xy[0], $xy[1])
      case_tuple = [ordered]@{
        in_out = 3
        inside_threshold = 158
        outside_threshold = 13
        use_background_color = 1
        invert = 1
        render_mode = 1
        interp_mode = 4
        power_bits = '0x40263bec'
        grad_r_bits = '0x3de0e0ff'
        grad_g_bits = '0x00000000'
        grad_b_bits = '0x3f6eeeef'
        bg_r_bits = '0x3f800000'
        bg_g_bits = '0x00000000'
        bg_b_bits = '0x00000000'
      }
      field_world = [ordered]@{
        base = $record['field_base']
        header = $record['field_header']
        rowbytes = $record['field_rowbytes']
        pixel_size = $record['field_pixel_size']
        channel_layout = 'PF_Pixel16 / 4xuint16 (A,G,R,B words)'
      }
      field_addr = $record['field_addr']
      field_raw_words_agrb = $record['field_raw_words_agrb']
      field_word_at_rcx_plus_2 = $record['field_word_at_rcx_plus_2']
      source_addr = $record['source_addr']
      source_raw_words_agrb = $record['source_raw_words_agrb']
      output_addr = $record['output_addr']
      pre_output_words_agrb = $record['pre_output_words_agrb']
      post_output_words_agrb = $record['post_output_words_agrb']
    }
  }
  return [ordered]@{
    schema = 'olmdistancegradation_case0026_16bpc_livefield_source_witness_return_v1'
    request_id = $RequestId
    status = 'answered'
    run = [ordered]@{
      run_id = $runIds[0]
      case_id = $ExpectedCaseFullId
      renderer = 'software'
      bits_per_channel = 16
      current_aex = [ordered]@{
        module = 'DistanceGradation.aex'
        path = 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex'
        sha256 = 'a1d317c0e18371494bc9c9933684593ca903eb6f3fe262ec06d5147b4c0bcbae'
        size = 26289664
        module_base = $recordList[0]['module_base']
      }
    }
    points = $points
  }
}

if($ParseOnly){
  if(-not $TracePath){ throw 'ParseOnly requires -TracePath' }
  (Convert-TraceToReturn $TracePath) | ConvertTo-Json -Depth 12
  exit 0
}

$isDesktop = $PSVersionTable.PSEdition -eq 'Desktop'
$isPs51 = $isDesktop -and $PSVersionTable.PSVersion.Major -eq 5
if(-not $SkipPowerShell51Relay -and -not $isPs51){
  if(-not (Test-Path -LiteralPath $PowerShell51 -PathType Leaf)){ throw "PowerShell 5.1 missing: $PowerShell51" }
  $relayArgs = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -PackageRoot "' + $PackageRoot + '" -WorkRoot "' + $WorkRoot + '" -AfterFx "' + $AfterFx + '" -Cdb "' + $Cdb + '" -PowerShell51 "' + $PowerShell51 + '" -SkipPowerShell51Relay'
  if($ParseOnly){ $relayArgs += ' -ParseOnly -TracePath "' + $TracePath + '"' }
  $relay = Start-Process -FilePath $PowerShell51 -ArgumentList $relayArgs -NoNewWindow -PassThru -Wait
  exit $relay.ExitCode
}

if(-not $PackageRoot){ $PackageRoot = Split-Path -Parent $PSCommandPath }
$caseRoot = Join-Path $PackageRoot 'case'
$jsx = Join-Path $caseRoot 'ae_render_single_case.jsx'
$requestDir = $caseRoot
$work = Join-Path $WorkRoot 'single_fresh_run'
$trace = Join-Path $work 'cdb_trace.log'
$stdout = Join-Path $work 'cdb_stdout.txt'
$stderr = Join-Path $work 'cdb_stderr.txt'
$returnJson = Join-Path $work 'RETURN_RUNTIME_TRACE.json'
$aeLog = Join-Path $work 'AE_SINGLE_CASE.log'
$aeResult = Join-Path $work 'AE_SINGLE_CASE_RESULT.json'
$cdbTemplate = Join-Path $PackageRoot 'case0026_livefield_source_witness.cdb.in'
$cdbScript = Join-Path $work 'case0026_livefield_source_witness.cdb'
foreach($path in @($AfterFx,$Cdb,$jsx,$cdbTemplate,(Join-Path $requestDir 'request_manifest.json'),(Join-Path $requestDir 'reference_manifest.json'),(Join-Path $requestDir 'input\case_0026_before_effects.png'))){
  if(-not (Test-Path -LiteralPath $path -PathType Leaf)){ throw "Missing packaged runner asset or tool: $path" }
}
if(-not (Test-Path -LiteralPath 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex' -PathType Leaf)){ throw "Pinned AEX missing: C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex" }
$aex = Get-Item -LiteralPath 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex'
$aexSha256 = (Get-FileHash -LiteralPath 'C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\DistanceGradation.aex' -Algorithm SHA256).Hash.ToLowerInvariant()
if($aex.Length -ne $ExpectedAexSize -or $aexSha256 -ne $ExpectedAexSha256){
  throw "Pinned AEX identity mismatch: size=$($aex.Length) sha256=$aexSha256"
}
New-Item -ItemType Directory -Force -Path $work | Out-Null
$env:OLM_AE_REQUEST_DIR = ($requestDir -replace '\\', '/')
$env:OLM_AE_CASE_ID = 'olmdistancegradation_extended__case_0026'
$env:OLM_AE_OUTPUT_DIR = $work
$env:OLM_AE_LOG_PATH = $aeLog
$env:OLM_AE_RESULT_JSON = $aeResult
$env:OLM_AE_PARAM_OVERRIDES_JSON = '{}'
$env:OLM_AE_FORCE_NEW_PROJECT = '1'
$env:OLM_AE_FORCE_SOFTWARE = '1'
$env:OLM_AE_DISABLE_PROJECT_COLOR_MANAGEMENT = '1'
$env:OLM_AE_KEEP_OPEN = '0'
$runId = 'dglfs_' + (Get-Date -Format 'yyyyMMddHHmmssfff')
$template = Get-Content -LiteralPath $cdbTemplate -Raw
$template = $template.Replace('WORKDIR', $work).Replace('RUN_ID', $runId)
$template | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$cdbArgs = '-cf "' + $cdbScript + '" "' + $AfterFx + '" -r "' + $jsx + '"'
$proc = Start-Process -FilePath $Cdb -ArgumentList $cdbArgs -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru -Wait
$parsed = Convert-TraceToReturn $trace
if($parsed.status -eq 'answered'){
  if(-not (Test-Path -LiteralPath $aeResult -PathType Leaf)){
    $parsed = New-Failure 'ae_result' 'AE result JSON missing after trace run' @('AE_SINGLE_CASE_RESULT.json') 'return' $runId
  } else {
    $result = Get-Content -LiteralPath $aeResult -Raw | ConvertFrom-Json
    if($result.status -ne 'ok' -or [int]$result.project_bits_per_channel -ne 16){
      $parsed = New-Failure 'ae_host_contract' "AE host contract mismatch: status=$($result.status) bits=$($result.project_bits_per_channel)" @('project_bits_per_channel') 'return' $runId
    } elseif(-not (Test-Path -LiteralPath $aeLog -PathType Leaf) -or -not ((Get-Content -LiteralPath $aeLog -Raw) -match 'gpuAccelType=SOFTWARE')){
      $parsed = New-Failure 'ae_host_contract' 'AE log does not confirm Software renderer' @('gpuAccelType=SOFTWARE') 'return' $runId
    }
  }
}
$parsed | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $returnJson -Encoding UTF8
$parsed | ConvertTo-Json -Depth 12
if($parsed.status -ne 'answered'){ exit 2 }
exit 0
