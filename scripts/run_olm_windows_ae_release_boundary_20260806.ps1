param(
  [string]$PackageRoot = (Split-Path -Parent (Split-Path -Parent $PSCommandPath)),
  [string]$AfterFX = 'C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe',
  [string]$OutputTemplate = 'OLM EXR 32 Float RGBA No Compression',
  [int]$TimeoutSeconds = 900
)
$ErrorActionPreference = 'Stop'
$Runner = Join-Path $PackageRoot 'scripts\ae_render_olm_windows_ae_release_boundary_20260806.jsx'
$ContractPath = Join-Path $PackageRoot 'BATCH_CONTRACT.json'
$ReturnName = 'RETURN_OLM_WINDOWS_AE_RELEASE_BOUNDARY_MINIMAL_20260806.zip'
$RunRoot = Join-Path (Split-Path $PackageRoot -Parent) 'olm_windows_boundary_run_20260806'
$Outputs = Join-Path $RunRoot 'outputs'
$CampaignId = 'olm_windows_all_plugins_reference_campaign_20260731_r5'
$DeployRoot = Join-Path $env:APPDATA "Adobe\Common\Plug-ins\7.0\MediaCore\OLM_Codex_Isolated\$CampaignId"

function Fail([string]$m) { throw "[FAIL_CLOSED] $m" }
function Hash([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function WriteJson([string]$p,$v) { $v | ConvertTo-Json -Depth 100 -Compress | Set-Content -LiteralPath $p -Encoding UTF8 }
function WaitFile([string]$p,[int]$seconds) { $d=(Get-Date).AddSeconds($seconds); while((Get-Date)-lt$d){if(Test-Path -LiteralPath $p -PathType Leaf){return};Start-Sleep -Milliseconds 200};Fail "timeout: $p" }
function StopAE { Get-Process AfterFX -ErrorAction SilentlyContinue | Stop-Process -Force; $d=(Get-Date).AddSeconds(20);while((Get-Process AfterFX -ErrorAction SilentlyContinue)-and(Get-Date)-lt$d){Start-Sleep -Milliseconds 250};if(Get-Process AfterFX -ErrorAction SilentlyContinue){Fail 'AfterFX remained running'} }
function Canon([string]$p) { [IO.Path]::GetFullPath($p).TrimEnd('\') }

foreach($p in @($AfterFX,$ContractPath,$Runner)){if(-not(Test-Path -LiteralPath $p -PathType Leaf)){Fail "missing: $p"}}
if(Get-Process AfterFX -ErrorAction SilentlyContinue){Fail 'close every AfterFX process before starting'}
$contract=Get-Content -LiteralPath $ContractPath -Raw | ConvertFrom-Json
if($contract.package_id -ne 'olm_windows_ae_release_boundary_minimal_20260806' -or @($contract.acquire).Count -ne 7){Fail 'unexpected contract'}
$aeInfo=(Get-Item -LiteralPath $AfterFX).VersionInfo
if($aeInfo.FileMajorPart-ne26-or$aeInfo.FileMinorPart-ne3-or$aeInfo.FilePrivatePart-ne87){Fail "AfterFX private build must be 26.3x87; got $($aeInfo.FileVersion)"}
$aeVersion='26.3x87'
$aeHash=Hash $AfterFX

# This directory is dedicated to this campaign. Reject links and remove only this exact scope.
$expectedSuffix="Adobe\Common\Plug-ins\7.0\MediaCore\OLM_Codex_Isolated\$CampaignId"
if(-not (Canon $DeployRoot).EndsWith($expectedSuffix,[StringComparison]::OrdinalIgnoreCase)){Fail 'deployment scope escape'}
if(Test-Path -LiteralPath $DeployRoot){$di=Get-Item -LiteralPath $DeployRoot -Force;if($di.Attributes -band [IO.FileAttributes]::ReparsePoint){Fail 'deployment root is a reparse point'};Remove-Item -LiteralPath $DeployRoot -Recurse -Force}
New-Item -ItemType Directory -Path $DeployRoot | Out-Null
$deployed=@{}
foreach($row in $contract.acquire){
  if($deployed.ContainsKey($row.plugin)){continue}
  $src=Join-Path $PackageRoot ($row.aex_member -replace '/','\');if((Hash $src)-ne $row.aex_sha256){Fail "AEX hash: $($row.plugin)"}
  $dir=Join-Path $DeployRoot $row.plugin;New-Item -ItemType Directory -Path $dir | Out-Null
  $dst=Join-Path $dir ([IO.Path]::GetFileName($src));[IO.File]::Copy($src,$dst,$false);if((Hash $dst)-ne $row.aex_sha256){Fail "deployed AEX hash: $($row.plugin)"};$deployed[$row.plugin]=$dst
}
if(Test-Path -LiteralPath $RunRoot){Remove-Item -LiteralPath $RunRoot -Recurse -Force};New-Item -ItemType Directory -Path $Outputs | Out-Null

foreach($row in $contract.acquire){
  StopAE
  $source=Join-Path $PackageRoot ($row.source_member -replace '/','\');$aex=$deployed[$row.plugin]
  if((Hash $source)-ne $row.source_sha256){Fail "source hash: $($row.row_id)"}
  $template=Join-Path $PackageRoot ($row.project_contract.input_interpretation.template_member -replace '/','\');if((Hash $template)-ne $row.project_contract.input_interpretation.template_sha256){Fail 'AEP template hash'}
  $rowOut=Join-Path $Outputs $row.row_id;New-Item -ItemType Directory -Path $rowOut | Out-Null
  $result=Join-Path $rowOut 'ae_result.json';$ready=Join-Path $rowOut 'ready.json';$go=Join-Path $rowOut 'continue.marker';$nonce=[Guid]::NewGuid().ToString('N')
  $env:OLM_BOUNDARY_ROOT=$PackageRoot;$env:OLM_BOUNDARY_ROW_ID=$row.row_id;$env:OLM_BOUNDARY_ROW_OUTPUT=$rowOut;$env:OLM_BOUNDARY_RESULT=$result;$env:OLM_BOUNDARY_READY=$ready;$env:OLM_BOUNDARY_CONTINUE=$go;$env:OLM_BOUNDARY_NONCE=$nonce;$env:OLM_BOUNDARY_OUTPUT_TEMPLATE=$OutputTemplate
  $started=(Get-Date).ToUniversalTime();$launch=Start-Process -FilePath $AfterFX -ArgumentList @('-r',$Runner) -PassThru
  try{WaitFile $ready $TimeoutSeconds;$rdy=Get-Content -LiteralPath $ready -Raw|ConvertFrom-Json
    if($rdy.nonce-ne$nonce-or$rdy.row_id-ne$row.row_id-or$rdy.ae_version-notlike'26.3*'-or$rdy.renderer_raw-ne1816-or$rdy.bits_per_channel-ne$row.depth-or[bool]$rdy.linear_blending){Fail "ready contract: $($row.row_id)"}
    $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($rdy.ae_pid)";if($null-eq$proc-or$proc.Name-ine'AfterFX.exe'-or(Canon $proc.ExecutablePath)-ine(Canon $AfterFX)){Fail 'fresh AE PID/path binding'}
    $gp=Get-Process -Id $rdy.ae_pid -ErrorAction Stop;$mod=@($gp.Modules|Where-Object{(Canon $_.FileName)-ieq(Canon $aex)});if($mod.Count-ne1){Fail "loaded AEX module binding: $($row.row_id)"}
    $moduleBase=('0x{0:x}' -f [Int64]$mod[0].BaseAddress);New-Item -ItemType File -Path $go | Out-Null;WaitFile $result $TimeoutSeconds
    $ae=Get-Content -LiteralPath $result -Raw|ConvertFrom-Json;if($ae.status-ne'ok'){Fail "AE row: $($row.row_id): $($ae.error)"}
    $deadline=(Get-Date).AddSeconds(30);while((Get-Process -Id $rdy.ae_pid -ErrorAction SilentlyContinue)-and(Get-Date)-lt$deadline){Start-Sleep -Milliseconds 250};StopAE
    foreach($pair in @(@('no_effect_source','no_effect.exr'),@('effect_on_source','effect_on.exr'))){$src=[string]$ae.($pair[0]);if(-not(Test-Path -LiteralPath $src -PathType Leaf)){Fail "missing render $src"};Move-Item -LiteralPath $src -Destination (Join-Path $rowOut $pair[1])}
    $att=[ordered]@{row_id=$row.row_id;execution_row_sha256=$row.execution_row_sha256;ae_version=$aeVersion;ae_executable_path=(Canon $AfterFX);ae_executable_sha256=$aeHash;ae_pid=[int]$rdy.ae_pid;ae_process_start_utc=$started.ToString('o');renderer_raw=[int]$ae.renderer_raw;bits_per_channel=[int]$ae.bits_per_channel;working_space_raw=$null;linear_blending=[bool]$ae.linear_blending;aex_path=(Canon $aex);aex_sha256=Hash $aex;module_base=$moduleBase;source_sha256=Hash $source;parameters_before=$ae.parameters_before;parameters_after=$ae.parameters_after;no_effect_sha256=Hash (Join-Path $rowOut 'no_effect.exr');effect_on_sha256=Hash (Join-Path $rowOut 'effect_on.exr')};WriteJson (Join-Path $rowOut 'attestation.json') $att
  }catch{StopAE;throw}
}
$zip=Join-Path (Split-Path $PackageRoot -Parent) $ReturnName;if(Test-Path -LiteralPath $zip){Remove-Item -LiteralPath $zip -Force};Compress-Archive -Path $Outputs -DestinationPath $zip
Write-Host "[OK] $zip"
