param(
  [string]$PackageRoot = (Split-Path -Parent $PSScriptRoot),
  [string]$WorkRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'work'),
  [switch]$ParseOnly,
  [string]$TracePath = ''
)

$ErrorActionPreference = 'Stop'
$requestId = 'olmdistancegradation_current_aex_same_run_exact_address_20260711'
$runId = 'dg-' + ([guid]::NewGuid().ToString('N'))
$cases = @(
  @{ Id = 'olmdistancegradation_extended__case_0010'; Suffix = '0010' },
  @{ Id = 'olmdistancegradation_extended__case_0011'; Suffix = '0011' }
)
$points = @(@{ X = 6; Y = 40 }, @{ X = 901; Y = 394 })
$required = @('run_id','case_id','x','y','entry_module_base','entry_inside_threshold','entry_outside_threshold','entry_case_tag','field_field_base','field_field_header','field_field_rowbytes','field_field_pixel_size','field_rcx','field_rcx_plus2_word','source_rdx','source_rdx_plus2_word','writer_output','writer_output_store_word','compose_xmm1_bits','compose_xmm2_bits','compose_xmm4_bits','compose_xmm5_bits','writer_final_writer_site','writer_final_writer_xmm_raw32','writer_word0','writer_word1','writer_word2','writer_word3')

function Convert-Marker([string]$line) {
  if ($line -notmatch '^OLMDG_(FIELD|SOURCE|COMPOSE|WRITER|ENTRY)\s+') { return $null }
  $kind = $line.Substring(6).Split(' ', 2)[0]
  $result = @{}
  $result['_kind'] = $kind
  foreach ($match in [regex]::Matches($line.Substring(7 + $kind.Length), '(?<key>[a-z0-9_]+)=(?<value>[^\s]+)')) {
    $result[$match.Groups['key'].Value] = $match.Groups['value'].Value
  }
  return $result
}

function New-Failure([string]$stage, [string]$reason, [object[]]$missing, [string]$last) {
  return [ordered]@{ status = 'exact_bind_failure'; failure = [ordered]@{ stage = $stage; reason = $reason; missing_fields = @($missing); last_observation = $last } }
}

function Convert-TraceToReturn([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { return New-Failure 'trace' "missing trace: $path" @('stdout') '' }
  $records = @{}
  $activeComposeKey = ''
  $activeWriterKey = ''
  $last = ''
  foreach ($line in Get-Content -LiteralPath $path) {
    $last = $line
    if ($activeComposeKey -and $line -match '^\s*xmm(?<lane>[1245])=(?<raw>[^\s]+)') {
      $records[$activeComposeKey]["compose_xmm$($Matches['lane'])_bits"] = $Matches['raw']
      continue
    }
    if ($activeWriterKey -and $line -match '^\s*xmm1=(?<raw>[^\s]+)') {
      $records[$activeWriterKey]['writer_final_writer_xmm_raw32'] = $Matches['raw']
      continue
    }
    $record = Convert-Marker $line
    if ($null -eq $record) { continue }
    if ($record['_kind'] -in @('FIELD','SOURCE','COMPOSE','WRITER','ENTRY')) {
      if (-not $record.ContainsKey('case_id')) { continue }
      $caseId = $record['case_id']
      if (-not $record.ContainsKey('x') -or -not $record.ContainsKey('y')) { continue }
      $key = "$($record['run_id'])|$($record['case_id'])|$($record['x'])|$($record['y'])"
      if (-not $records.ContainsKey($key)) { $records[$key] = [ordered]@{ run_id = $record['run_id']; case_id = $caseId; x = $record['x']; y = $record['y'] } }
      if ($record['_kind'] -eq 'ENTRY') { $records[$key]['entry_module_base'] = $record['module_base'] }
      foreach ($item in $record.GetEnumerator()) { if ($item.Key -ne '_kind') { $records[$key]["$($record['_kind'].ToLowerInvariant())_$($item.Key)"] = $item.Value } }
      if ($record['_kind'] -eq 'COMPOSE') { $activeComposeKey = $key; $activeWriterKey = '' }
      if ($record['_kind'] -eq 'WRITER') { $activeWriterKey = $key; $activeComposeKey = '' }
    }
  }
  $recordList = @($records.Values)
  $expected = @('case_0010|6|40','case_0010|901|394','case_0011|6|40','case_0011|901|394')
  $seen = @{}
  $missing = @()
  foreach ($record in $recordList) {
    foreach ($key in $required) { if (-not $record.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$record[$key])) { $missing += "$($record['case_id'])/$($record['x']),$($record['y']):$key" } }
    if ($record['case_id'] -eq 'case_0010' -and ($record['entry_case_tag'] -ne '10' -or $record['entry_inside_threshold'] -ne '63' -or $record['entry_outside_threshold'] -ne '82')) { $missing += 'case_0010_fingerprint_mismatch' }
    if ($record['case_id'] -eq 'case_0011' -and ($record['entry_case_tag'] -ne '11' -or $record['entry_inside_threshold'] -ne '348' -or $record['entry_outside_threshold'] -ne '0')) { $missing += 'case_0011_fingerprint_mismatch' }
    $seen["$($record['case_id'])|$($record['x'])|$($record['y'])"] = $true
  }
  foreach ($key in $expected) { if (-not $seen.ContainsKey($key)) { $missing += "missing:$key" } }
  $runIds = @($recordList | ForEach-Object { $_['run_id'] } | Select-Object -Unique)
  if ($recordList.Count -ne 4) { $missing += "record_count=$($recordList.Count)" }
  if ($runIds.Count -ne 1) { $missing += 'shared_run_id' }
  if ($missing.Count -gt 0) { return New-Failure 'typed_tuple' 'one or more live fields or exact witnesses are missing' $missing $last }
  $witnesses = @($recordList | ForEach-Object {
    [ordered]@{
      run_id = $_['run_id']; case_id = $_['case_id']; xy = @([int]$_.x,[int]$_.y)
      current_aex = [ordered]@{ module = 'DistanceGradation.aex'; module_base = $_['entry_module_base'] }
      case_fingerprint = [ordered]@{ case_tag = [int]$_.entry_case_tag; inside_threshold = [int]$_.entry_inside_threshold; outside_threshold = [int]$_.entry_outside_threshold; source = 'dword [RBX+0xb8]/[RBX+0xbc] at callback entry' }
      field_world = [ordered]@{ base = $_['field_field_base']; header = $_['field_field_header']; rowbytes = [int]$_.field_field_rowbytes; pixel_size = [int]$_.field_field_pixel_size; channel_layout = 'PF_Pixel16 / 4xuint16' }
      rcx_field_addr = $_['field_rcx']; rcx_field_word_at_plus_2 = $_['field_rcx_plus2_word']
      rdx_source_addr = $_['source_rdx']; rdx_source_word_at_plus_2 = $_['source_rdx_plus2_word']
      output_addr = $_['writer_output']; output_store_word = $_['writer_output_store_word']
      compose_scalar_bits = [ordered]@{ xmm1 = $_['compose_xmm1_bits']; xmm2 = $_['compose_xmm2_bits']; xmm4 = $_['compose_xmm4_bits']; xmm5 = $_['compose_xmm5_bits'] }
      final_writer = [ordered]@{ site = $_['writer_final_writer_site']; xmm = $_['writer_final_writer_xmm_raw32']; pf16_words = @($_['writer_word0'], $_['writer_word1'], $_['writer_word2'], $_['writer_word3']) }
    }
  })
  return [ordered]@{ status = 'answered'; run_id = $runIds[0]; witnesses = $witnesses }
}

if ($ParseOnly) {
  if (-not $TracePath) { throw 'ParseOnly requires -TracePath' }
  $parsed = Convert-TraceToReturn $TracePath
  $parsed | ConvertTo-Json -Depth 12
  exit 0
}

$work = Join-Path $WorkRoot "olmdg_same_run_$runId"
New-Item -ItemType Directory -Force -Path $work | Out-Null
$trace = Join-Path $work 'cdb_stdout.txt'
$return = Join-Path $work 'RETURN_RUNTIME_TRACE.json'
$cdb = 'C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe'
$afterFx = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe'
$queue = Join-Path $PackageRoot 'scripts\ae_render_olmdistancegradation_current_aex_queue_20260711.jsx'
$cdbScript = Join-Path $work 'olmdg_same_run.cdb'
$runMarker = $runId
$cdbText = @'
.effmach amd64
.expr /s masm
sxi 80000003
sxe ld:DistanceGradation.aex
 r @$t2 = 0xdead
bu DistanceGradation+0x1170480 " r @$t4 = dwo(@rbx+0xb8); r @$t5 = dwo(@rbx+0xbc); r @$t2 = 0xdead; .if (@$t4 == 63 && @$t5 == 82) { r @$t2 = 10 } .else { .if (@$t4 == 348 && @$t5 == 0) { r @$t2 = 11 } }; r @$t1 = poi(@rsp+0x28)-@r8*0x3c00-@edx*8; r @$t8 = @rdi-@$t1; r @$t6 = (@$t8 % 0x3c00) / 8; r @$t7 = @$t8 / 0x3c00; .if (@$t2 == 10) { .printf \"OLMDG_ENTRY run_id=__RUN_MARKER__ case_id=case_0010 case_tag=10 inside_threshold=%u outside_threshold=%u x=%u y=%u module_base=%p output_base=%p param_block=%p\\n\", @$t4, @$t5, @$t6, @$t7, @rip-0x1170480, @$t1, @rbx); } .else { .if (@$t2 == 11) { .printf \"OLMDG_ENTRY run_id=__RUN_MARKER__ case_id=case_0011 case_tag=11 inside_threshold=%u outside_threshold=%u x=%u y=%u module_base=%p output_base=%p param_block=%p\\n\", @$t4, @$t5, @$t6, @$t7, @rip-0x1170480, @$t1, @rbx); } }"
bu DistanceGradation+0x117057d ".if (@rdi == @$t1 + 40*0x3c00 + 6*8 || @rdi == @$t1 + 394*0x3c00 + 901*8) { r @$t8 = @rdi-@$t1; r @$t6 = (@$t8 % 0x3c00) / 8; r @$t7 = @$t8 / 0x3c00; .if (@$t2 == 10) { .printf \"OLMDG_FIELD run_id=__RUN_MARKER__ case_id=case_0010 x=%u y=%u rcx=%p rcx_plus2_word=%hu field_base=%p field_header=%p field_rowbytes=15360 field_pixel_size=8\\n\", @$t6, @$t7, @rcx, poi(@rcx+2), @r10+0x18, @r10); } .else { .if (@$t2 == 11) { .printf \"OLMDG_FIELD run_id=__RUN_MARKER__ case_id=case_0011 x=%u y=%u rcx=%p rcx_plus2_word=%hu field_base=%p field_header=%p field_rowbytes=15360 field_pixel_size=8\\n\", @$t6, @$t7, @rcx, poi(@rcx+2), @r10+0x18, @r10); } } }"
bu DistanceGradation+0x11705f1 ".if (@rdi == @$t1 + 40*0x3c00 + 6*8 || @rdi == @$t1 + 394*0x3c00 + 901*8) { r @$t8 = @rdi-@$t1; r @$t6 = (@$t8 % 0x3c00) / 8; r @$t7 = @$t8 / 0x3c00; .if (@$t2 == 10) { .printf \"OLMDG_SOURCE run_id=__RUN_MARKER__ case_id=case_0010 x=%u y=%u rdx=%p rdx_plus2_word=%hu\\n\", @$t6, @$t7, @rdx, poi(@rdx+2)); } .else { .if (@$t2 == 11) { .printf \"OLMDG_SOURCE run_id=__RUN_MARKER__ case_id=case_0011 x=%u y=%u rdx=%p rdx_plus2_word=%hu\\n\", @$t6, @$t7, @rdx, poi(@rdx+2)); } } }"
bu DistanceGradation+0x1170808 ".if (@rdi == @$t1 + 40*0x3c00 + 6*8 || @rdi == @$t1 + 394*0x3c00 + 901*8) { r @$t8 = @rdi-@$t1; r @$t6 = (@$t8 % 0x3c00) / 8; r @$t7 = @$t8 / 0x3c00; .if (@$t2 == 10) { .printf \"OLMDG_COMPOSE run_id=__RUN_MARKER__ case_id=case_0010 x=%u y=%u\\n\", @$t6, @$t7; } .else { .if (@$t2 == 11) { .printf \"OLMDG_COMPOSE run_id=__RUN_MARKER__ case_id=case_0011 x=%u y=%u\\n\", @$t6, @$t7; } }; r xmm1; r xmm2; r xmm4; r xmm5; }"
bu DistanceGradation+0x1170814 ".if (@rdi == @$t1 + 40*0x3c00 + 6*8 || @rdi == @$t1 + 394*0x3c00 + 901*8) { r @$t8 = @rdi-@$t1; r @$t6 = (@$t8 % 0x3c00) / 8; r @$t7 = @$t8 / 0x3c00; .if (@$t2 == 10) { .printf \"OLMDG_WRITER run_id=__RUN_MARKER__ case_id=case_0010 x=%u y=%u output=%p output_store_word=%hu final_writer_site=DistanceGradation+0x1170814 word0=%hu word1=%hu word2=%hu word3=%hu\\n\", @$t6, @$t7, @rdi, poi(@rdi), poi(@rdi), poi(@rdi+2), poi(@rdi+4), poi(@rdi+6)); } .else { .if (@$t2 == 11) { .printf \"OLMDG_WRITER run_id=__RUN_MARKER__ case_id=case_0011 x=%u y=%u output=%p output_store_word=%hu final_writer_site=DistanceGradation+0x1170814 word0=%hu word1=%hu word2=%hu word3=%hu\\n\", @$t6, @$t7, @rdi, poi(@rdi), poi(@rdi), poi(@rdi+2), poi(@rdi+4), poi(@rdi+6)); } }; r xmm1; }"
.logopen /t __TRACE_PATH__
g
.logclose
q
'@
$cdbText = $cdbText.Replace('__RUN_MARKER__', $runMarker).Replace('__TRACE_PATH__', $trace)
$cdbText | Set-Content -LiteralPath $cdbScript -Encoding ASCII
$env:OLM_DG_QUEUE_POINTS = '6,40|901,394'
$env:OLM_DG_RUN_ID = $runId
$env:OLM_DG_REQUEST_DIR = Join-Path $PackageRoot 'handoff\ae_pixel_validation_20260618\requests\ae_pixel_bitdepth16_olmdistancegradation_extended_exact_20260625'
$proc = Start-Process -FilePath $cdb -ArgumentList @('-cf',$cdbScript,$afterFx,'-r',$queue) -RedirectStandardOutput $trace -RedirectStandardError ($trace + '.err') -NoNewWindow -PassThru -Wait
$parsed = Convert-TraceToReturn $trace
$parsed | Add-Member -NotePropertyName request_id -NotePropertyValue $requestId -Force
$parsed | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $return -Encoding UTF8
$parsed | ConvertTo-Json -Depth 12
if ($parsed.status -ne 'answered') { exit 2 }
