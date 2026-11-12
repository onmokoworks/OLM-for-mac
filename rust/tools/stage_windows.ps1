<#[Synopsis]
Build the Windows workspace and copy the ten DLLs under their original names.
This is staging only. Use a fresh output directory outside any host installation.
#>
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$OutputDir)
$ErrorActionPreference = 'Stop'
$rustRoot = Split-Path $PSScriptRoot -Parent
$destination = [IO.Path]::GetFullPath($OutputDir)
if ($destination -match '(?i)(^|[\\/])(MediaCore|Plug-ins|Program Files(?: \(x86\))?)([\\/]|$)') {
    throw 'Choose a staging directory, not an application installation directory.'
}
$plugins = [ordered]@{
    color_keep = 'ColorKeep'
    olm_distance_gradation = 'DistanceGradation'
    olm_blur = 'OLMBlur'
    olm_color_key = 'OLMColorKey'
    olm_directional_blur = 'OLMDirectionalBlur'
    olm_kirakira = 'OLMKiraKira'
    olm_radial_blur = 'OLMRadialBlur'
    olm_smoother = 'OLMSmoother'
    olm_smoother2 = 'OLMSmoother2'
    olm_toon_dilate = 'OLMToonDilate'
}
foreach ($name in $plugins.Values) {
    if (Test-Path -LiteralPath (Join-Path $destination "$name.aex")) {
        throw "Refusing to overwrite $name.aex; choose a fresh staging directory."
    }
}
$oldTarget = $env:CARGO_TARGET_DIR
Push-Location $rustRoot
try {
    Remove-Item Env:CARGO_TARGET_DIR -ErrorAction SilentlyContinue
    & cargo build --release --workspace --offline
    if ($LASTEXITCODE -ne 0) { throw "Cargo build failed ($LASTEXITCODE)." }
    foreach ($library in $plugins.Keys) {
        if (!(Test-Path -LiteralPath "target/release/$library.dll")) {
            throw "Missing build output: $library.dll"
        }
    }
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    $manifest = foreach ($library in $plugins.Keys) {
        $source = (Resolve-Path "target/release/$library.dll").Path
        $output = Join-Path $destination ($plugins[$library] + '.aex')
        Copy-Item -LiteralPath $source -Destination $output
        $sourceHash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
        $outputHash = (Get-FileHash -LiteralPath $output -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($sourceHash -ne $outputHash) { throw "Copy verification failed: $output" }
        [pscustomobject]@{ name = $plugins[$library]; source = $source; path = $output; sha256 = $outputHash; bytes = (Get-Item -LiteralPath $output).Length }
    }
    $manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $destination 'manifest.json') -Encoding UTF8
    $manifest | Format-Table name, bytes, sha256
} finally {
    Pop-Location
    if ($null -eq $oldTarget) { Remove-Item Env:CARGO_TARGET_DIR -ErrorAction SilentlyContinue }
    else { $env:CARGO_TARGET_DIR = $oldTarget }
}
