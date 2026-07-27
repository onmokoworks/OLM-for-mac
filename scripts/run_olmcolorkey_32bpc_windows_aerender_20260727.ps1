param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

$ErrorActionPreference = "Stop"
$aepx = Join-Path $Root "olmcolorkey_all9_windows.aepx"
$output = Join-Path $Root "output"
$etw = Join-Path $Root "etw"
$etl = Join-Path $etw "olmcolorkey_all9_kernel.etl"
$csv = Join-Path $etw "olmcolorkey_all9_kernel.csv"
$stdout = Join-Path $Root "aerender_stdout.txt"
$stderr = Join-Path $Root "aerender_stderr.txt"
$summary = Join-Path $Root "run_summary.json"
$aerender = "C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\aerender.exe"
$aex = "C:\Program Files\Adobe\Common\Plug-ins\7.0\MediaCore\OLM\OLMColorKey.aex"

if (@(Get-Process AfterFX -ErrorAction SilentlyContinue).Count -ne 0 -or
    @(Get-Process "AfterFX.com" -ErrorAction SilentlyContinue).Count -ne 0) {
    throw "Adobe process already running"
}
if (@(Get-ChildItem -LiteralPath $output -File).Count -ne 0) {
    throw "output directory is not empty"
}

$started = $false
$startedUtc = (Get-Date).ToUniversalTime().ToString("o")
try {
    & xperf.exe -on PROC_THREAD+LOADER -f $etl | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "xperf start failed: $LASTEXITCODE"
    }
    $started = $true
    $proc = Start-Process -FilePath $aerender `
        -ArgumentList @("-project", "`"$aepx`"", "-v", "ERRORS_AND_PROGRESS") `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -PassThru
    $aerenderPid = $proc.Id
    $proc.WaitForExit()
    $proc.Refresh()
    if (-not $proc.HasExited) {
        throw "aerender did not reach an exited state"
    }
    [int]$exitCode = $proc.ExitCode
}
finally {
    if ($started) {
        & xperf.exe -stop | Out-Null
    }
}

& xperf.exe -i $etl -o $csv -a dumper | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "xperf dump failed: $LASTEXITCODE"
}

$record = [ordered]@{
    started_utc = $startedUtc
    completed_utc = (Get-Date).ToUniversalTime().ToString("o")
    aerender_pid = $aerenderPid
    aerender_exit_code = $exitCode
    aerender_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $aerender).Hash.ToLower()
    aex_path = $aex
    aex_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $aex).Hash.ToLower()
    aepx_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $aepx).Hash.ToLower()
    output_count = @(Get-ChildItem -LiteralPath $output -Filter *.exr -File).Count
    etl_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $etl).Hash.ToLower()
    csv_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $csv).Hash.ToLower()
    stdout_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stdout).Hash.ToLower()
    stderr_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $stderr).Hash.ToLower()
}
if ($record.output_count -ne 18) {
    throw "expected 18 EXR outputs, got $($record.output_count)"
}
$record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $summary -Encoding utf8
$record | ConvertTo-Json -Compress
if ($exitCode -ne 0) {
    exit $exitCode
}
