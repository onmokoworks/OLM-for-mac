param(
  [Parameter(Mandatory=$true)][string]$AfterFX,
  [Parameter(Mandatory=$true)][string]$ColorKeyAex,
  [Parameter(Mandatory=$true)][string]$ToonDilateAex,
  [Parameter(Mandatory=$false)][string]$OutputDir = "",
  [Parameter(Mandatory=$false)][int]$TimeoutSeconds = 300
)

$ErrorActionPreference = "Stop"
$PackageRoot = Split-Path -Parent $PSCommandPath
$FixtureJsx = Join-Path $PackageRoot "fixture\ae_generate_32bpc_typed_procedural_fixture.jsx"
$RunRoot = if ($OutputDir) { $OutputDir } else { Join-Path $PackageRoot "run" }
$ReturnJson = Join-Path $RunRoot "return_manifest.json"
$ExpectedTemplate = "OLM EXR 32 Float"
$ExpectedAe = "26.3"
$FixtureSha = "85129d1cc50be9b8ad9b6945e0c7cc07c49fdafe3b99c49f323b49d364ec4ca8"
$ExpectedContract = ConvertFrom-Json @'
{"manifest_kind":"olm_32bpc_typed_procedural_fixture","project_bits_per_channel":32,"working_space":"None","linear_blending":false,"dimensions":[64,64],"frame":0,"source_policy":"AE-generated solids only; no footage imported","render_policy":"same comp, only branch enabled state changes","source_layers":[{"name":"solid_background","kind":"solid","bounds":[0,0,64,64],"rgb":[0,0,0],"alpha":1.0},{"name":"rect_integer_a25","kind":"solid","bounds":[4,4,20,16],"rgb":[1,0,0],"alpha":0.25},{"name":"rect_integer_a50","kind":"solid","bounds":[28,4,20,16],"rgb":[0,1,0],"alpha":0.5},{"name":"rect_integer_a75","kind":"solid","bounds":[4,28,20,16],"rgb":[0,0,1],"alpha":0.75},{"name":"rect_integer_a100","kind":"solid","bounds":[28,28,20,16],"rgb":[1,1,1],"alpha":1.0}],"output_names":{"no_effect":"effect_no_effect_00000.exr","effect_on":"effect_effect_on_00000.exr"}}
'@
$Cases = ConvertFrom-Json @'
[{"id":"olmcolorkey_typed_procedural_64x64","effect":"OLM Color Key","plugin_name":"OLMColorKey.aex","plugin_sha256":"9c6cca226a52d35ce7833fcc4c0f914f6b15b3abe0202e0957ba97ba3bb2cf2c"},{"id":"olmtoondilate_typed_procedural_64x64","effect":"OLM Toon Dilate","plugin_name":"OLMToonDilate.aex","plugin_sha256":"c05db8c118029ff3216d3cae8e6423e2eb41ca8f56de2fb3668db81b9b8c32b3"}]
'@

function Write-Json([string]$Path, $Value) {
  $Value | ConvertTo-Json -Depth 50 | Set-Content -Encoding UTF8 $Path
}

function Fail([string]$Status, [string]$Message) {
  New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
  Write-Json $ReturnJson ([ordered]@{
    kind = "olm_32bpc_typed_procedural_render_record"
    schema = 1
    platform = "windows"
    record_role = "return"
    status = $Status
    error = $Message
    required_ae_major_minor = $ExpectedAe
    output_template = $ExpectedTemplate
    fixture_jsx_sha256 = $FixtureSha
    cases = @()
  })
  throw "$Status`: $Message"
}

function Wait-ForFile([string]$Path, [int]$Seconds) {
  $deadline = (Get-Date).AddSeconds($Seconds)
  while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $Path -PathType Leaf) { return }
    Start-Sleep -Milliseconds 500
  }
  throw "timeout waiting for $Path"
}

function Stop-AfterFX {
  Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue | Stop-Process -Force
  Start-Sleep -Seconds 2
}

if (Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue) {
  Fail "afterfx_running" "Close After Effects before running the typed procedural package"
}
foreach ($path in @($AfterFX, $FixtureJsx)) {
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    Fail "missing_asset" "Missing packaged runner asset or tool: $path"
  }
}
$PluginMap = @{
  "OLMColorKey.aex" = $ColorKeyAex
  "OLMToonDilate.aex" = $ToonDilateAex
}
$PluginRecords = @{}
foreach ($case in $Cases) {
  $pluginPath = $PluginMap[$case.plugin_name]
  if (-not (Test-Path -LiteralPath $pluginPath -PathType Leaf)) {
    Fail "missing_plugin" "$($case.plugin_name) missing"
  }
  $hash = (Get-FileHash -LiteralPath $pluginPath -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $case.plugin_sha256) {
    Fail "plugin_hash_mismatch" "$($case.plugin_name) sha256 $hash != $($case.plugin_sha256)"
  }
  $PluginRecords[$case.id] = [ordered]@{
    name = $case.plugin_name
    path = (Resolve-Path $pluginPath).Path
    sha256 = $hash
  }
}

New-Item -ItemType Directory -Force -Path $RunRoot | Out-Null
$Records = @()
$LastAeVersion = ""
foreach ($case in $Cases) {
  Stop-AfterFX
  if (Get-Process -Name "AfterFX" -ErrorAction SilentlyContinue) {
    Fail "afterfx_shutdown_failed" "AfterFX still running before case $($case.id)"
  }
  $CaseRoot = Join-Path $RunRoot ("cases\" + $case.id)
  New-Item -ItemType Directory -Force -Path $CaseRoot | Out-Null
  $ProjectPath = Join-Path $CaseRoot "fixture.aep"
  $ResultPath = Join-Path $CaseRoot "fixture_result.json"
  $ManifestPath = Join-Path $CaseRoot "fixture_manifest.json"
  foreach ($path in @($ProjectPath, $ResultPath, $ManifestPath, (Join-Path $CaseRoot "effect_no_effect_00000.exr"), (Join-Path $CaseRoot "effect_effect_on_00000.exr"))) {
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
  }
  $env:OLM_AE_TYPED_FIXTURE_OUTPUT_DIR = $CaseRoot
  $env:OLM_AE_TYPED_FIXTURE_TEMPLATE = $ExpectedTemplate
  $env:OLM_AE_TYPED_FIXTURE_PROJECT_PATH = $ProjectPath
  $env:OLM_AE_TYPED_FIXTURE_EFFECT = $case.effect
  $env:OLM_AE_TYPED_FIXTURE_OVERWRITE = "1"
  $process = Start-Process -FilePath $AfterFX -ArgumentList ('-r "' + $FixtureJsx + '"') -PassThru
  try {
    Wait-ForFile $ResultPath $TimeoutSeconds
  } catch {
    try { if ($process -and -not $process.HasExited) { $process | Stop-Process -Force } } catch {}
    Fail "render_timeout" "$($case.id) did not produce fixture_result.json within $TimeoutSeconds seconds"
  }
  $result = Get-Content -LiteralPath $ResultPath -Raw | ConvertFrom-Json
  if ($result.status -ne "ok") {
    Stop-AfterFX
    Fail "render_failed" "$($case.id) returned status=$($result.status) error=$($result.error)"
  }
  $LastAeVersion = $result.ae_version
  if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Stop-AfterFX
    Fail "missing_manifest" "$($case.id) did not produce fixture_manifest.json"
  }
  $manifest = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
  if ($result.ae_version -notlike "$ExpectedAe*") {
    Stop-AfterFX
    Fail "wrong_ae_version" "$($case.id) expected AE $ExpectedAe, got $($result.ae_version)"
  }
  if ($manifest.kind -ne $ExpectedContract.manifest_kind) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) manifest kind mismatch"
  }
  if ($manifest.project_bits_per_channel -ne $ExpectedContract.project_bits_per_channel) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) bitsPerChannel mismatch"
  }
  if ($manifest.working_space -ne $ExpectedContract.working_space) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) working space mismatch"
  }
  if ([bool]$manifest.linear_blending -ne [bool]$ExpectedContract.linear_blending) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) linear blending mismatch"
  }
  if (($manifest.dimensions | ConvertTo-Json -Compress) -ne ($ExpectedContract.dimensions | ConvertTo-Json -Compress)) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) dimensions mismatch"
  }
  if ($manifest.frame -ne $ExpectedContract.frame) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) frame mismatch"
  }
  if ($manifest.source_policy -ne $ExpectedContract.source_policy -or $manifest.render_policy -ne $ExpectedContract.render_policy) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) source/render policy mismatch"
  }
  if (($manifest.source_layers | ConvertTo-Json -Depth 20 -Compress) -ne ($ExpectedContract.source_layers | ConvertTo-Json -Depth 20 -Compress)) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) source_layers mismatch"
  }
  if (($manifest.outputs | ConvertTo-Json -Compress) -ne ($ExpectedContract.output_names | ConvertTo-Json -Compress)) {
    Stop-AfterFX
    Fail "contract_mismatch" "$($case.id) output_names mismatch"
  }
  $NoEffect = Join-Path $CaseRoot $ExpectedContract.output_names.no_effect
  $EffectOn = Join-Path $CaseRoot $ExpectedContract.output_names.effect_on
  foreach ($path in @($NoEffect, $EffectOn, $ProjectPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      Stop-AfterFX
      Fail "missing_artifact" "$($case.id) missing required artifact $path"
    }
  }
  $Records += [ordered]@{
    id = $case.id
    effect = $case.effect
    plugin = $PluginRecords[$case.id]
    fixture_contract = [ordered]@{
      manifest_kind = $ExpectedContract.manifest_kind
      project_bits_per_channel = $ExpectedContract.project_bits_per_channel
      working_space = $ExpectedContract.working_space
      linear_blending = [bool]$ExpectedContract.linear_blending
      dimensions = @($ExpectedContract.dimensions)
      frame = $ExpectedContract.frame
      source_policy = $ExpectedContract.source_policy
      render_policy = $ExpectedContract.render_policy
      source_layers = $ExpectedContract.source_layers
      output_names = [ordered]@{
        no_effect = $ExpectedContract.output_names.no_effect
        effect_on = $ExpectedContract.output_names.effect_on
      }
    }
    outputs = [ordered]@{
      no_effect = [ordered]@{
        path = (Resolve-Path $NoEffect).Path.Substring((Resolve-Path $RunRoot).Path.Length + 1).Replace("\", "/")
        sha256 = (Get-FileHash -LiteralPath $NoEffect -Algorithm SHA256).Hash.ToLowerInvariant()
      }
      effect_on = [ordered]@{
        path = (Resolve-Path $EffectOn).Path.Substring((Resolve-Path $RunRoot).Path.Length + 1).Replace("\", "/")
        sha256 = (Get-FileHash -LiteralPath $EffectOn -Algorithm SHA256).Hash.ToLowerInvariant()
      }
    }
  }
  Stop-AfterFX
}

$Record = [ordered]@{
  kind = "olm_32bpc_typed_procedural_render_record"
  schema = 1
  platform = "windows"
  record_role = "return"
  status = "rendered"
  required_ae_major_minor = $ExpectedAe
  ae_version = $LastAeVersion
  output_template = $ExpectedTemplate
  fixture_jsx_sha256 = $FixtureSha
  cases = $Records
}
Write-Json $ReturnJson $Record
$Zip = Join-Path (Split-Path $RunRoot -Parent) "olm_windows_32bpc_typed_procedural_fixture_return.zip"
if (Test-Path -LiteralPath $Zip) { Remove-Item -LiteralPath $Zip -Force }
Compress-Archive -Path (Join-Path $RunRoot "*") -DestinationPath $Zip
Write-Host "OK return=$Zip"
