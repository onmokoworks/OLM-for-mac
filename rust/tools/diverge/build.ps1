param(
    [Parameter(Mandatory=$true)][string]$Tree,
    [Parameter(Mandatory=$true)][string]$Target,
    [switch]$FeatureOff
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$repo = [IO.Path]::GetFullPath((Join-Path $here '../../..'))
$treePath = [IO.Path]::GetFullPath($Tree)
$targetPath = [IO.Path]::GetFullPath($Target)
$localPrefix = [IO.Path]::GetFullPath((Join-Path $here 'local')) + [IO.Path]::DirectorySeparatorChar
$ownedPrefix = [IO.Path]::GetFullPath($here) + [IO.Path]::DirectorySeparatorChar
if (!$treePath.StartsWith($localPrefix, [StringComparison]::OrdinalIgnoreCase) -or !$targetPath.StartsWith($ownedPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Tree must be below diverge/local and target below diverge'
}
if (Test-Path -LiteralPath $treePath) { throw 'Choose a new private tree directory' }
New-Item -ItemType Directory -Force "$treePath/rust/plugins", "$treePath/rust/crates" | Out-Null
# Read-only build inputs through exact junctions; never enumerate or delete them.
foreach ($name in @('core','mac','ucrtmath')) {
    New-Item -ItemType Junction -Path (Join-Path $treePath $name) -Target (Join-Path $repo $name) | Out-Null
}
foreach ($name in @('olm-directional-blur','olm-distance-gradation')) {
    $dst = Join-Path $treePath "rust/plugins/$name"
    New-Item -ItemType Directory -Force "$dst/tests" | Out-Null
    Copy-Item "$repo/rust/plugins/$name/Cargo.toml", "$repo/rust/plugins/$name/build.rs" $dst
    Copy-Item "$repo/rust/plugins/$name/src" "$dst/src" -Recurse
    Copy-Item "$repo/rust/plugins/$name/tests/reference.cpp" "$dst/tests/reference.cpp"
}
foreach ($name in @('olm-core','olm-math','olm-ae')) {
    $dst = Join-Path $treePath "rust/crates/$name"
    New-Item -ItemType Directory -Force $dst | Out-Null
    Copy-Item "$repo/rust/crates/$name/Cargo.toml" $dst
    Copy-Item "$repo/rust/crates/$name/src" "$dst/src" -Recurse
    foreach ($file in @('build.rs','reference.cpp')) {
        if (Test-Path "$repo/rust/crates/$name/$file") { Copy-Item "$repo/rust/crates/$name/$file" $dst }
    }
}
$manifest = Get-Content "$repo/rust/Cargo.toml" -Raw
$manifest = $manifest.Replace('"crates/*", "plugins/*", "tools/*"','"crates/*", "plugins/*"')
[IO.File]::WriteAllText("$treePath/rust/Cargo.toml", $manifest)
Copy-Item "$repo/rust/Cargo.lock" "$treePath/rust/Cargo.lock"
# Build through the witness owned-process runner to bound Cargo and descendants.
$buildArgs = @('--manifest-path', "$treePath/rust/Cargo.toml", '--release', '--offline', '-p', 'olm-directional-blur', '-p', 'olm-distance-gradation', '--jobs', '2')
if (!$FeatureOff) { $buildArgs += @('--features', 'olm-directional-blur/stage-dump,olm-distance-gradation/stage-dump') }
$savedEnv = @{}
foreach ($key in @('CARGO_TARGET_DIR','CARGO_PROFILE_RELEASE_DEBUG','RUSTFLAGS')) {
    $savedEnv[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
try {
$env:CARGO_TARGET_DIR = $targetPath
$env:CARGO_PROFILE_RELEASE_DEBUG = '0'
$env:RUSTFLAGS = '-C link-arg=/Brepro -C link-arg=/DEBUG:NONE -C link-arg=/INCREMENTAL:NO'
python "$here/build_owned.py" --out "$treePath/build-log" @buildArgs
if ($LASTEXITCODE -ne 0) { throw "Build failed: $treePath/build-log" }
} finally {
    foreach ($key in $savedEnv.Keys) { [Environment]::SetEnvironmentVariable($key, $savedEnv[$key], 'Process') }
}
foreach ($name in @('olm_directional_blur','olm_distance_gradation')) {
    Copy-Item "$targetPath/release/$name.dll" "$treePath/$name.aex"
}
Write-Output "Built both plugins in $treePath"
