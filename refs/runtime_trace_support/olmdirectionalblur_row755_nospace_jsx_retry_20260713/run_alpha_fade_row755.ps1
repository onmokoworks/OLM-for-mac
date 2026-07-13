[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$AexPath,
  [string]$CdbPath='C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe',
  [string]$AfterFxPath='C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$WorkRoot=''
)
$ErrorActionPreference='Stop'
if(-not $WorkRoot){$WorkRoot=Join-Path (Split-Path -Parent $PSCommandPath) 'work'}
$requestId='olmdirectionalblur_alpha_fade_fullrender_row755_20260712'
$expectedHash='d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e'
$expectedSize=56832L
$runId='dblur-row755-'+[guid]::NewGuid().ToString('N')
$chunkPixels=16
$chunkCount=21
$focusPixels=334
$work=Join-Path $WorkRoot $runId
New-Item -ItemType Directory -Force -Path $work | Out-Null
function Finish([string]$status,[hashtable]$extra,[int]$code) {
  $body=[ordered]@{schema=1;request_id=$requestId;status=$status;run_id=$runId}
  foreach($item in $extra.GetEnumerator()){$body[$item.Key]=$item.Value}
  $json=$body|ConvertTo-Json -Depth 16
  $json|Set-Content -LiteralPath (Join-Path $work 'RETURN_RUNTIME_TRACE.json') -Encoding UTF8
  $json
  exit $code
}
if(!(Test-Path -LiteralPath $AexPath -PathType Leaf)){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='AEX absent'}} 2}
$aex=Get-Item -LiteralPath $AexPath
$hash=(Get-FileHash -Algorithm SHA256 -LiteralPath $aex.FullName).Hash.ToLowerInvariant()
if($aex.Length -ne $expectedSize -or $hash -ne $expectedHash){Finish 'exact_bind_failure' @{failure=@{stage='aex_identity';reason='size or SHA256 mismatch';sha256=$hash;size=$aex.Length}} 2}
foreach($exe in @($CdbPath,$AfterFxPath)){if(!(Test-Path -LiteralPath $exe -PathType Leaf)){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='required executable absent'}} 2}}
if(Get-Process -Name 'AfterFX' -ErrorAction SilentlyContinue){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='After Effects must be fully closed before this run'}} 2}
$trace=Join-Path $work 'cdb_output.txt'
$stderr=Join-Path $work 'cdb_stderr.txt'
$readyMarker=Join-Path $work 'ae_ready.marker'
$continueMarker=Join-Path $work 'ae_continue.marker'
$env:OLM_AE_REQUEST_DIR=Join-Path $PSScriptRoot 'case'; $env:OLM_AE_CASE_ID='db_angle0_alpha_fade_hard_edges'; $env:OLM_AE_INPUT_ALPHA_MODE='PREMULTIPLIED'; $env:OLM_AE_FORCE_SOFTWARE='1'; $env:OLM_AE_FORCE_NEW_PROJECT='1'; $env:OLM_AE_KEEP_OPEN='0'; $env:OLM_AE_PAUSE_BEFORE_RENDER='1'; $env:OLM_AE_READY_MARKER=$readyMarker; $env:OLM_AE_CONTINUE_MARKER=$continueMarker; $env:OLM_AE_OUTPUT_DIR=Join-Path $work 'render'; $env:OLM_AE_LOG_PATH=Join-Path $work 'ae_render.log'; $env:OLM_AE_RESULT_JSON=Join-Path $work 'ae_render_result.json'
New-Item -ItemType Directory -Force -Path $env:OLM_AE_OUTPUT_DIR | Out-Null
$chunkDir=Join-Path $work 'chunks'
New-Item -ItemType Directory -Force -Path $chunkDir | Out-Null
$jsx=Join-Path $PSScriptRoot 'case\ae_render_single_case.jsx'
if(!(Test-Path -LiteralPath $jsx)){Finish 'exact_bind_failure' @{failure=@{stage='package';reason='case runner missing'}} 3}
$jsxLaunchDir=Join-Path $env:PUBLIC ("OLMTrace\"+$runId)
New-Item -ItemType Directory -Force -Path $jsxLaunchDir | Out-Null
$jsxLaunch=Join-Path $jsxLaunchDir 'runner.jsx'
Copy-Item -LiteralPath $jsx -Destination $jsxLaunch -Force
if($jsxLaunch -match '\s'){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='no-space JSX launch path invariant failed';jsx_path=$jsxLaunch}} 3}
$aeProc=Start-Process -FilePath $AfterFxPath -ArgumentList ('-m -r "'+$jsxLaunch+'"') -PassThru
$deadline=(Get-Date).AddSeconds(180)
while((Get-Date) -lt $deadline -and !(Test-Path -LiteralPath $readyMarker)){Start-Sleep -Milliseconds 250}
if(!(Test-Path -LiteralPath $readyMarker)){Finish 'exact_bind_failure' @{failure=@{stage='ae_pause';reason='ready marker not written'}} 4}
$module=$null
$deadline=(Get-Date).AddSeconds(30)
while((Get-Date) -lt $deadline -and $null -eq $module){
  try {$module=(Get-Process -Id $aeProc.Id -ErrorAction Stop).Modules | Where-Object {$_.FileName -ieq $aex.FullName} | Select-Object -First 1} catch {}
  if($null -eq $module){Start-Sleep -Milliseconds 250}
}
if($null -eq $module){Finish 'exact_bind_failure' @{failure=@{stage='module_lookup';reason='hash-pinned AEX not loaded at ready marker';pid=$aeProc.Id;aex_path=$aex.FullName}} 4}
$base=('0x{0:x}' -f $module.BaseAddress.ToInt64())
$template=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'row755_capture.cdb.in') -Raw
$chunkCommands=New-Object System.Text.StringBuilder
for($i=0;$i -lt $chunkCount;$i++){
  $pixels=[Math]::Min($chunkPixels,$focusPixels-($i*$chunkPixels))
  $destBytes=$pixels*16
  $scalarBytes=$pixels*4
  $destOffset=$i*$chunkPixels*16
  $scalarOffset=$i*$chunkPixels*4
  $destPath=Join-Path $chunkDir (('destination_{0:D3}.bin' -f $i))
  $denomPath=Join-Path $chunkDir (('denominator_{0:D3}.bin' -f $i))
  $alphaPath=Join-Path $chunkDir (('alpha_valid_{0:D3}.bin' -f $i))
  [void]$chunkCommands.AppendLine(('r @$t4=@$t1+'+$destOffset))
  [void]$chunkCommands.AppendLine(('r @$t5=@$t4+'+($destBytes-1)))
  [void]$chunkCommands.AppendLine(('.writemem "'+$destPath+'" @$t4 @$t5'))
  [void]$chunkCommands.AppendLine(('r @$t4=@$t2+'+$scalarOffset))
  [void]$chunkCommands.AppendLine(('r @$t5=@$t4+'+($scalarBytes-1)))
  [void]$chunkCommands.AppendLine(('.writemem "'+$denomPath+'" @$t4 @$t5'))
  [void]$chunkCommands.AppendLine(('r @$t4=@$t3+'+$scalarOffset))
  [void]$chunkCommands.AppendLine(('r @$t5=@$t4+'+($scalarBytes-1)))
  [void]$chunkCommands.AppendLine(('.writemem "'+$alphaPath+'" @$t4 @$t5'))
}
$capturePath=Join-Path $work 'capture_at_5554.cdb'
$captureHeader=@(
  'r @$t6=@rbx',
  ('.printf "DBR_STAGE run_id='+$runId+' pid=%u stage=0x5554 before_normalization=1 params=%p worker_hits=%u worker_params=%p rowdriver_calls=%u row_params=%p row_start=%u row_end=%u row755_covered=%u params_mismatch=%u\n", @$tpid, @$t6, @$t11, @$t10, @$t8, @$t7, @$t4, @$t5, @$t12, @$t13'),
  '.printf "DBR_PROVENANCE params=%p destination_base=%p destination_source=params+0x8090 denominator_base=%p denominator_source=params+0x8080 alpha_valid_base=%p alpha_valid_source=params+0x8088 row0=%u col0=%u stride=%u row=755 x_start=747 x_end=1080\n", @$t6, poi(@$t6+0x8090), poi(@$t6+0x8080), poi(@$t6+0x8088), dwo(@$t6+0x8098), dwo(@$t6+0x809c), dwo(@$t6+0x80a0)',
  'r @$t1=poi(@$t6+0x8090)+(((755-dwo(@$t6+0x8098))*dwo(@$t6+0x80a0)+747-dwo(@$t6+0x809c))*16)',
  'r @$t2=poi(@$t6+0x8080)+(((755-dwo(@$t6+0x8098))*dwo(@$t6+0x80a0)+747-dwo(@$t6+0x809c))*4)',
  'r @$t3=poi(@$t6+0x8088)+(((755-dwo(@$t6+0x8098))*dwo(@$t6+0x80a0)+747-dwo(@$t6+0x809c))*4)'
)
$captureFooter=@(('.printf "DBR_CAPTURE_END run_id='+$runId+'\n"'),'.kill','q')
@($captureHeader)+@($chunkCommands.ToString() -split "`r?`n" | Where-Object {$_})+@($captureFooter) | Set-Content -LiteralPath $capturePath -Encoding ASCII
if($capturePath -match '\s'){Finish 'exact_bind_failure' @{failure=@{stage='preflight';reason='capture script path contains whitespace';capture_path=$capturePath}} 3}
$cmd=$template.Replace('__RUN__',$runId).Replace('__BASE__',$base).Replace('__CAPTURE_SCRIPT__',$capturePath)
$cmdPath=Join-Path $work 'row755_capture.cdb'; $cmd|Set-Content -LiteralPath $cmdPath -Encoding ASCII
$proc=Start-Process -FilePath $CdbPath -ArgumentList @('-cf',$cmdPath,'-p',$aeProc.Id) -RedirectStandardOutput $trace -RedirectStandardError $stderr -NoNewWindow -PassThru
$deadline=(Get-Date).AddSeconds(60)
while((Get-Date) -lt $deadline){if((Test-Path $trace) -and ((Get-Content $trace -Raw) -match 'DBR_BREAKPOINTS_READY')){break};Start-Sleep -Milliseconds 250}
if(!(Test-Path $trace) -or -not ((Get-Content $trace -Raw) -match 'DBR_BREAKPOINTS_READY')){Finish 'exact_bind_failure' @{failure=@{stage='attach';reason='absolute breakpoints not armed';pid=$aeProc.Id;base=$base}} 4}
Set-Content -LiteralPath $continueMarker -Value 'continue' -Encoding ASCII
$proc|Wait-Process
$text=if(Test-Path $trace){Get-Content -LiteralPath $trace -Raw}else{''}
$stage=[regex]::Match($text,'DBR_STAGE run_id=(\S+) pid=(\d+) stage=(\S+) before_normalization=(\d+) params=(\S+) worker_hits=(\d+) worker_params=(\S+) rowdriver_calls=(\d+) row_params=(\S+) row_start=(\d+) row_end=(\d+) row755_covered=(\d+) params_mismatch=(\d+)')
$prov=[regex]::Match($text,'DBR_PROVENANCE params=(\S+) destination_base=(\S+) .* denominator_base=(\S+) .* alpha_valid_base=(\S+) .* row0=(\d+) col0=(\d+) stride=(\d+) row=755 x_start=747 x_end=1080')
$rowMatches=[regex]::Matches($text,'DBR_ROW_RANGE run_id=(\S+) pid=(\d+) call=(\d+) start=(\d+) end=(\d+) params=(\S+)')
$ranges=@($rowMatches | ForEach-Object {@{run_id=$_.Groups[1].Value;pid=[int]$_.Groups[2].Value;call=[int]$_.Groups[3].Value;start=[int]$_.Groups[4].Value;end=[int]$_.Groups[5].Value;params=$_.Groups[6].Value}} | Sort-Object start,call)
$rangesValid=$stage.Success -and ($ranges.Count -eq [int]$stage.Groups[8].Value) -and ($ranges.Count -gt 0)
$row755Seen=$false
if($rangesValid){
  for($i=0;$i -lt $ranges.Count;$i++){
    $r=$ranges[$i]
    if($r.run_id -ne $runId -or $r.pid -ne [int]$stage.Groups[2].Value -or $r.params -ne $stage.Groups[5].Value -or $r.end -le $r.start){$rangesValid=$false}
    if($i -eq 0){if($r.start -ne 0){$rangesValid=$false}}elseif($r.start -ne $ranges[$i-1].end){$rangesValid=$false}
    if($r.start -le 755 -and $r.end -gt 755){$row755Seen=$true}
  }
  if($ranges[0].start -ne [int]$stage.Groups[10].Value -or $ranges[-1].end -ne [int]$stage.Groups[11].Value){$rangesValid=$false}
}
$required=@($stage.Success,$prov.Success,$stage.Groups[1].Value -eq $runId,$stage.Groups[3].Value -eq '0x5554',$stage.Groups[4].Value -eq '1',[int]$stage.Groups[6].Value -gt 0,$stage.Groups[7].Value -eq $stage.Groups[5].Value,[int]$stage.Groups[8].Value -gt 0,$stage.Groups[9].Value -eq $stage.Groups[5].Value,[int]$stage.Groups[12].Value -eq 1,[int]$stage.Groups[13].Value -eq 0,$rangesValid,$row755Seen,$prov.Groups[1].Value -eq $stage.Groups[5].Value,[int]$prov.Groups[5].Value -le 755,[int]$prov.Groups[6].Value -le 747,[int]$prov.Groups[7].Value -eq 2206)
$chunkFailures=New-Object System.Collections.Generic.List[string]
foreach($spec in @(@('destination','row755_destination_rgba_f32_le.bin',16),@('denominator','row755_denominator_f32_le.bin',4),@('alpha_valid','row755_alpha_valid_f32_le.bin',4))){
  $combined=New-Object System.Collections.Generic.List[byte]
  for($i=0;$i -lt $chunkCount;$i++){
    $pixels=[Math]::Min($chunkPixels,$focusPixels-($i*$chunkPixels))
    $chunk=Join-Path $chunkDir (('{0}_{1:D3}.bin' -f $spec[0],$i))
    $expected=$pixels*$spec[2]
    if(!(Test-Path -LiteralPath $chunk)){$chunkFailures.Add(('missing '+$chunk));continue}
    $data=[IO.File]::ReadAllBytes($chunk)
    if($data.Length -ne $expected){$chunkFailures.Add(('wrong_size '+$chunk+' expected='+$expected+' actual='+$data.Length));continue}
    foreach($byte in $data){$combined.Add($byte)}
  }
  if($combined.Count -eq ($focusPixels*$spec[2])){[IO.File]::WriteAllBytes((Join-Path $work $spec[1]),$combined.ToArray())}
}
$required += (Test-Path -LiteralPath (Join-Path $work 'row755_destination_rgba_f32_le.bin') -and (Get-Item (Join-Path $work 'row755_destination_rgba_f32_le.bin')).Length -eq 5344)
$required += (Test-Path -LiteralPath (Join-Path $work 'row755_denominator_f32_le.bin') -and (Get-Item (Join-Path $work 'row755_denominator_f32_le.bin')).Length -eq 1336)
$required += (Test-Path -LiteralPath (Join-Path $work 'row755_alpha_valid_f32_le.bin') -and (Get-Item (Join-Path $work 'row755_alpha_valid_f32_le.bin')).Length -eq 1336)
$listing=Join-Path $work 'capture_listing.json'
Get-ChildItem -LiteralPath $work -File -Recurse | Select-Object FullName,Length | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $listing -Encoding UTF8
if($required -contains $false -or $chunkFailures.Count -gt 0){Finish 'exact_bind_failure' @{failure=@{stage='binding';reason='stage/address/row/run binding or exact-size chunk artifact missing';cdb_exit_code=$proc.ExitCode;chunk_failures=@($chunkFailures);ranges=$ranges;capture_listing='capture_listing.json'};trace=$text} 4}
$artifacts=[ordered]@{}
foreach($spec in @(@('row755_destination_rgba_f32_le.bin',5344,1336),@('row755_denominator_f32_le.bin',1336,334),@('row755_alpha_valid_f32_le.bin',1336,334))){$p=Join-Path $work $spec[0];$artifacts[$spec[0]]=@{path=$spec[0];bytes=(Get-Item $p).Length;words=[int]$spec[2];sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant()}}
Finish 'answered' @{pid=[int]$stage.Groups[2].Value;work_dir=$work;artifact_root='.';capture_listing='capture_listing.json';aex=@{path='OLMDirectionalBlur.aex';sha256=$hash;size=$aex.Length};call_schedule=@{worker_entry='0x4d84';worker_hits=[int]$stage.Groups[6].Value;worker_params=$stage.Groups[7].Value;rowdriver_entry='0x38d0';params=$stage.Groups[5].Value;row_start=[int]$stage.Groups[10].Value;row_end=[int]$stage.Groups[11].Value;rowdriver_calls=[int]$stage.Groups[8].Value;ranges=$ranges};stage=@{module='OLMDirectionalBlur.aex';offset='0x5554';identity='first instruction of internal normalization loop';before_normalization=$true};address_provenance=@{params=$prov.Groups[1].Value;destination=@{base=$prov.Groups[2].Value;source='params+0x8090';row0=[int]$prov.Groups[5].Value;col0=[int]$prov.Groups[6].Value;stride=[int]$prov.Groups[7].Value;row=755;x_start=747;x_end=1080};denominator=@{base=$prov.Groups[3].Value;source='params+0x8080';row=755;x_start=747;x_end=1080};alpha_valid=@{base=$prov.Groups[4].Value;source='params+0x8088';row=755;x_start=747;x_end=1080}};artifacts=$artifacts} 0
