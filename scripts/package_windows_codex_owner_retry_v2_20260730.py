#!/usr/bin/env python3
"""Build and validate the consolidated 20260730 Windows owner retry v2 request."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)
REQUEST_SCHEMA = "olm_windows_owner_retry_request_v2_20260730"
RETURN_SCHEMA = "olm_windows_owner_retry_return_v2_20260730"
ORIGINAL_NAME = "immutable/olm_windows_batch_20260728_r1.zip"
ORIGINAL_SHA256 = "809c3760c4e5b1f96e6747f2e9188435b3f2caaca6f229cf0ba061384cbc84ab"
REJECTED_RETURN_SHA256 = "764182ff612a0d6ab7d5f48ac63aa110f5d6de7682561231980a3a6ffbc066a9"
CHECKSUM_RE = re.compile(r"^([0-9a-f]{64})  ([^\r\n]+)$")
ENTRYPOINT = "RUN_WINDOWS_CODEX_OWNER_RETRY_V2_20260730.ps1"
RETURN_PACKAGER = "pack_windows_owner_retry_return_v2_20260730.py"


class ContractError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")


def safe_name(name: str) -> str:
    if not name or "\\" in name or name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise ContractError(f"unsafe archive member: {name!r}")
    path = PurePosixPath(name)
    if any(part in ("", ".", "..") for part in path.parts):
        raise ContractError(f"unsafe archive member: {name!r}")
    return name


def read_zip(path: Path) -> dict[str, bytes]:
    try:
        with zipfile.ZipFile(path) as archive:
            result: dict[str, bytes] = {}
            folded: set[str] = set()
            for info in archive.infolist():
                if info.is_dir():
                    raise ContractError(f"directory member forbidden: {info.filename}")
                name = safe_name(info.filename)
                if name.casefold() in folded:
                    raise ContractError(f"duplicate Windows member: {name}")
                folded.add(name.casefold())
                mode = info.external_attr >> 16
                if info.create_system == 3 and stat.S_IFMT(mode) and not stat.S_ISREG(mode):
                    raise ContractError(f"non-regular member forbidden: {name}")
                result[name] = archive.read(info)
    except zipfile.BadZipFile as exc:
        raise ContractError(f"invalid ZIP: {path}") from exc
    return result


def validate_checksums(members: dict[str, bytes]) -> None:
    try:
        raw = members["CHECKSUMS.sha256"].decode("ascii")
    except (KeyError, UnicodeDecodeError) as exc:
        raise ContractError("missing or non-ASCII CHECKSUMS.sha256") from exc
    if not raw.endswith("\n"):
        raise ContractError("CHECKSUMS.sha256 must end with LF")
    rows = [CHECKSUM_RE.fullmatch(line) for line in raw.splitlines()]
    if any(row is None for row in rows):
        raise ContractError("malformed CHECKSUMS.sha256 row")
    parsed = [(row.group(2), row.group(1)) for row in rows if row]
    names = [name for name, _ in parsed]
    expected = sorted(name for name in members if name != "CHECKSUMS.sha256")
    if names != expected:
        raise ContractError("CHECKSUMS.sha256 must list every other member once in lexical order")
    for name, expected_sha in parsed:
        if sha256(members[name]) != expected_sha:
            raise ContractError(f"checksum mismatch: {name}")


def validate_original(data: bytes) -> None:
    if sha256(data) != ORIGINAL_SHA256:
        raise ContractError("immutable original r1 request SHA-256 mismatch")
    with tempfile.NamedTemporaryFile(suffix=".zip") as handle:
        handle.write(data)
        handle.flush()
        members = read_zip(Path(handle.name))
    validate_checksums(members)
    manifest = json.loads(members["BATCH_MANIFEST.json"])
    if manifest.get("batch_id") != "olm_windows_batch_20260728_r1" or len(manifest.get("jobs", [])) != 3:
        raise ContractError("immutable original r1 manifest identity mismatch")


def instructions() -> bytes:
    return b"""# Windows Codex owner retry v2 -- 2026-07-30

## History and purpose

This is the next consolidated retry for the immutable
`olm_windows_batch_20260728_r1.zip`. The 20260730 owner return is rejected
fail-closed: its parent checksum inventory is not canonical/admissible, and all
three lanes report `exact_bind_failure`. Preserve both historical archives
unchanged. The rejected return may guide diagnosis but must not be relabelled,
sanitized, or used to reconstruct the original request.

The purpose is one bounded Windows/After Effects run that resolves the remaining
questions with raw same-run evidence. Render completion, wrapper success,
breakpoint arming, a nonzero count, or CLI agreement cannot establish what the
owned After Effects process read or wrote.

CLI exact never substitutes for AE exact.

Raw runtime observations and the no-effect/effect images must share one
request identity, run ID, exact-owned AfterFX PID, installed/loaded AEX
path+SHA+base, project/case, renderer, bit depth, source identity, and artifact
identity.

## Start and execution

Use only `RUN_WINDOWS_CODEX_OWNER_RETRY_V2_20260730.ps1`.

1. Run it with `-Mode Prepare -WorkRoot <new-empty-path>`. This validates this
   request and the embedded immutable r1, expands all three jobs, and stops.
2. Make the bounded Windows-local runner/debugger patches described below inside
   that work root. Preserve diffs, hashes, parse/smoke commands, stdout, stderr,
   and exit codes. Do not alter the immutable embedded ZIP.
3. Ensure no AfterFX process is already running and no modal is present. The
   entrypoint assumes a clean, noninteractive desktop; it never dismisses or
   answers a modal.
4. Run the same entrypoint with `-Mode Execute -WorkRoot <same-path>` only after
   explicit user release of the HOLD gate. Supply the exact token formed from
   `I_RELEASE_HOLD_OLM_WINDOWS_OWNER_RETRY_20260730_V2`, the request-manifest
   SHA-256, and the prepared-state SHA-256 printed by `Prepare`. It runs all
   three lane `run.ps1`
   files sequentially, retains every attempt, and continues after lane failure.
5. Assemble and validate exactly one consolidated return with
   `py -3 pack_windows_owner_retry_return_v2_20260730.py STAGE_DIR RETURN.zip`,
   then run `-Mode ValidateReturn -ReturnZip <path>`. The validator reconstructs
   the entire archive with the bundled algorithm and requires byte-for-byte
   equality. Return no per-lane/small ZIPs.

## Lane 1 -- Radial cleanup

Keep the useful retry-3 same-run typed sampler evidence. Repair only the
ownership cleanup/completion boundary. A successful answer requires clean CDB
detach/exit plus cleanup that targets only the uniquely owned PID after exact
identity revalidation. If ownership is absent, stale, reused, or ambiguous,
record `exact_bind_failure` and terminate nothing. Include raw trace/events, AE
result, no-effect control, effect output, process identities, and cleanup record.
Do not infer final writeback, export causality, CLI exactness, or AE exactness
from the sampler witness alone.

## Lane 2 -- Directional store plus same-run render

Retain the same-thread target-store repair and direct four-byte PF8 store.
Complete the no-effect control and effect render in the same owned AE run and
bind them to the store observation. Require the exact coordinate `(494,169)`,
writer RVA, target address, debugger thread/slot state, raw pre/post bytes,
result JSON, and both images. A store without the paired same-run render is
`exact_bind_failure`; image presence without the raw store is also failure.

## Lane 3 -- DG raw-entry / typed-coordinate diagnostic

At RVA `0x1170480`, record raw entry hits before coordinate filtering. Preserve
RIP, RCX, RDX, R8, R9, `poi(RSP+0x20)`, `poi(RSP+0x28)`,
`poi(RSP+0x30)`, bounded stack trace, `u`, `!address`, and `lmvm`. Report raw and
typed counts separately. Use the observed raw-entry argument layout to diagnose
and repair the typed coordinate contract; do not change the AEX algorithm.
Raw>0/typed=0 is diagnostic, not an answer. Raw=0 with completed render requires
grounded dispatch/RVA investigation. Include raw-entry and typed-coordinate
records plus the same-run no-effect/effect artifacts under the common binding.

## Exact ownership, modal, and cleanup rules

Launch a new AfterFX process and record its PID, creation time, executable path,
command line, parent/launcher identity, and run nonce. Attach only after all
fields match. Never attach to or kill a pre-existing or ambiguous process.
Cleanup may detach/terminate only registered PIDs after revalidation of the same
identity tuple. On mismatch, timeout, missing identity, unexpected prompt, or
modal suspicion: preserve diagnostics, fail closed, and leave unrelated
processes untouched. Do not automate/dismiss/accept modals, change Adobe
preferences, clear/bypass caches, or broadly kill Adobe/CDB processes.

## Claim and return gate

`answered` is lane-local and narrow. No lane may claim AE exact unless one
same-run contract contains a no-effect control and effect output with a raw
comparison, and all process/module/case/artifact bindings agree. CLI results are
diagnostic only. Whole-plugin, cross-version, algorithm, or final-output claims
remain out of scope unless directly witnessed here.

Return exactly one canonical ZIP after all lanes are terminal. It must contain
`RETURN_MANIFEST.json`, `REQUEST_MANIFEST.json`, `RETURN_CONTRACT.json`,
`CHECKSUMS.sha256`, and direct non-ZIP evidence under each lane directory. JSON
is strict UTF-8 without BOM. `CHECKSUMS.sha256` covers every other member exactly
once in lexicographic member-name order and is validated before delivery. ZIP
members themselves must also be written in lexicographic order with DOS epoch
`1980-01-01 00:00:00`, deflate compression, Unix create-system metadata, and
regular-file mode `0644`; the validator rejects any metadata drift.
"""


def entrypoint() -> bytes:
    return rb'''[CmdletBinding()]
param(
  [ValidateSet("Prepare","Execute","ValidateReturn")]
  [string]$Mode = "Prepare",
  [Parameter(Mandatory=$true)][string]$WorkRoot,
  [string]$ReturnZip,
  [string]$HoldReleaseToken
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$requestRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $requestRoot "REQUEST_MANIFEST.json"
$originalZip = Join-Path $requestRoot "immutable\olm_windows_batch_20260728_r1.zip"
$expectedOriginal = "809c3760c4e5b1f96e6747f2e9188435b3f2caaca6f229cf0ba061384cbc84ab"
$releasePhrase = "I_RELEASE_HOLD_OLM_WINDOWS_OWNER_RETRY_20260730_V2"

function Fail([string]$Message) { throw "FAIL_CLOSED: $Message" }
function Hash([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function Assert-NoAfterFX {
  $existing = @(Get-CimInstance Win32_Process -Filter "Name='AfterFX.exe'")
  if ($existing.Count -ne 0) { Fail "AfterFX.exe is already running; exact ownership is unavailable" }
}
function Assert-NoReparseTree([string]$Target, [string]$Root) {
  $rootExpanded = [IO.Path]::GetFullPath($Root)
  $volumeRoot = [IO.Path]::GetPathRoot($rootExpanded)
  $rootFull = $(if ($rootExpanded -ceq $volumeRoot) { $volumeRoot } else { $rootExpanded.TrimEnd('\') })
  $targetFull = [IO.Path]::GetFullPath($Target)
  $rootPrefix = $(if ($rootFull -ceq $volumeRoot) { $volumeRoot } else { $rootFull + '\' })
  if ($targetFull -cne $rootFull -and -not $targetFull.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    Fail "path escapes WorkRoot: $Target"
  }
  if (-not (Test-Path -LiteralPath $volumeRoot)) { Fail "volume root missing: $volumeRoot" }
  if ((Get-Item -LiteralPath $volumeRoot -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
    Fail "reparse-point volume root forbidden: $volumeRoot"
  }
  $current = $volumeRoot
  $rootParts = @()
  if ($rootFull -cne $volumeRoot) {
    $rootParts = $rootFull.Substring($volumeRoot.Length).Split('\', [StringSplitOptions]::RemoveEmptyEntries)
  }
  foreach ($part in $rootParts) {
    $current = Join-Path $current $part
    if (-not (Test-Path -LiteralPath $current)) { Fail "WorkRoot ancestor missing: $current" }
    if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
      Fail "reparse-point WorkRoot ancestor forbidden: $current"
    }
  }
  $current = $rootFull
  $parts = @()
  if ($targetFull.Length -gt $rootFull.Length) {
    $parts = $targetFull.Substring($rootFull.Length).TrimStart('\').Split('\')
  }
  foreach ($part in @("") + $parts) {
    if ($part) { $current = Join-Path $current $part }
    if (-not (Test-Path -LiteralPath $current)) { Fail "path component missing: $current" }
    if ((Get-Item -LiteralPath $current -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
      Fail "reparse-point path component forbidden: $current"
    }
  }
}
function Assert-CanonicalChecksums([string]$Root) {
  $lines = @(Get-Content -LiteralPath (Join-Path $Root "CHECKSUMS.sha256") -Encoding Ascii)
  $actual = @()
  foreach ($line in $lines) {
    if ($line -notmatch '^([0-9a-f]{64})  (.+)$') { Fail "malformed checksum row" }
    $actual += $Matches[2]
    $path = Join-Path $Root ($Matches[2] -replace '/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Fail "missing checksummed member: $($Matches[2])" }
    if ((Hash $path) -ne $Matches[1]) { Fail "checksum mismatch: $($Matches[2])" }
  }
  $expected = @(Get-ChildItem -LiteralPath $Root -File -Recurse | ForEach-Object {
    $_.FullName.Substring($Root.Length + 1).Replace('\','/')
  } | Where-Object { $_ -ne "CHECKSUMS.sha256" } | Sort-Object -CaseSensitive)
  if (($actual -join "`n") -cne ($expected -join "`n")) { Fail "checksum inventory/order is not canonical" }
}

# Validate the complete request root before trusting its manifest, entrypoint, or embedded r1.
Assert-CanonicalChecksums $requestRoot
$requestManifestHash = Hash $manifestPath
if ((Hash $originalZip) -ne $expectedOriginal) { Fail "immutable original r1 SHA-256 mismatch" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne "olm_windows_owner_retry_request_v2_20260730") { Fail "request schema mismatch" }
$expectedLaneIds = @(
  "radial_cleanup_20260730_v2",
  "directional_store_render_20260730_v2",
  "dg_raw_typed_coordinate_20260730_v2"
)
if (($manifest.lanes.id -join "`n") -cne ($expectedLaneIds -join "`n")) { Fail "lane whitelist mismatch" }

if ($Mode -eq "Prepare") {
  if (Test-Path -LiteralPath $WorkRoot) {
    if (@(Get-ChildItem -LiteralPath $WorkRoot -Force).Count -ne 0) { Fail "Prepare requires a new empty work root" }
  } else { New-Item -ItemType Directory -Path $WorkRoot | Out-Null }
  Assert-NoReparseTree $WorkRoot $WorkRoot
  Assert-NoAfterFX
  $r1 = Join-Path $WorkRoot "immutable_r1"
  Expand-Archive -LiteralPath $originalZip -DestinationPath $r1
  Assert-CanonicalChecksums $r1
  foreach ($lane in $manifest.lanes) {
    $childZip = Join-Path $r1 ($lane.original_child_package -replace '/', '\')
    if ((Hash $childZip) -ne $lane.original_child_sha256) { Fail "child SHA mismatch: $($lane.id)" }
    $laneRoot = Join-Path $WorkRoot ("lanes\" + $lane.id)
    New-Item -ItemType Directory -Path $laneRoot | Out-Null
    Assert-NoReparseTree $laneRoot $WorkRoot
    Expand-Archive -LiteralPath $childZip -DestinationPath $laneRoot
  }
  Copy-Item -LiteralPath (Join-Path $requestRoot "README_FIRST.md") -Destination $WorkRoot
  $prepared = [ordered]@{
    schema = "olm_windows_owner_retry_prepared_v2_20260730"
    request_manifest_sha256 = $requestManifestHash
    original_r1_sha256 = $expectedOriginal
    lane_ids = $expectedLaneIds
  }
  $preparedPath = Join-Path $WorkRoot "PREPARED_STATE_20260730_V2.json"
  $preparedJson = $prepared | ConvertTo-Json -Depth 5
  [IO.File]::WriteAllText($preparedPath, $preparedJson + "`n", (New-Object Text.UTF8Encoding($false)))
  $preparedHash = Hash $preparedPath
  Set-Content -LiteralPath (Join-Path $WorkRoot "PREPARED_STATE_20260730_V2.sha256") -Value $preparedHash -Encoding Ascii
  Write-Host "PREPARED_ONLY request_manifest_sha256=$requestManifestHash prepared_state_sha256=$preparedHash"
  Write-Host "Apply bounded patches, preserve diffs/tests, then obtain an explicit HOLD token bound to both hashes."
  exit 0
}

if ($Mode -eq "ValidateReturn") {
  if (-not $ReturnZip) { Fail "-ReturnZip is required" }
  $validate = Join-Path $requestRoot "validate_windows_owner_retry_return_v2_20260730.py"
  & py -3 $validate $ReturnZip
  if ($LASTEXITCODE -ne 0) { Fail "return validator rejected archive" }
  exit 0
}

$preparedPath = Join-Path $WorkRoot "PREPARED_STATE_20260730_V2.json"
$preparedHashPath = Join-Path $WorkRoot "PREPARED_STATE_20260730_V2.sha256"
if (-not (Test-Path -LiteralPath $preparedPath -PathType Leaf)) { Fail "prepared state missing" }
if (-not (Test-Path -LiteralPath $preparedHashPath -PathType Leaf)) { Fail "prepared hash missing" }
Assert-NoReparseTree $preparedPath $WorkRoot
Assert-NoReparseTree $preparedHashPath $WorkRoot
$preparedHash = Hash $preparedPath
if ((Get-Content -LiteralPath $preparedHashPath -Raw -Encoding Ascii).Trim() -cne $preparedHash) { Fail "prepared state hash drift" }
$prepared = Get-Content -LiteralPath $preparedPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($prepared.request_manifest_sha256 -cne $requestManifestHash) { Fail "prepared/request binding mismatch" }
$expectedToken = "$releasePhrase`:$requestManifestHash`:$preparedHash"
if (-not $HoldReleaseToken -or $HoldReleaseToken -cne $expectedToken) { Fail "explicit HOLD release token missing or not bound to request/prepared state" }

$results = @()
for ($index = 0; $index -lt $expectedLaneIds.Count; $index++) {
  $laneId = $expectedLaneIds[$index]
  Assert-NoAfterFX
  $run = Join-Path $WorkRoot ("lanes\" + $laneId + "\run.ps1")
  if (-not (Test-Path -LiteralPath $run -PathType Leaf)) {
    Fail "missing whitelisted lane entrypoint: $laneId"
  }
  Assert-NoReparseTree $run $WorkRoot
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $run
  $code = $LASTEXITCODE
  $cleanupPath = Join-Path $WorkRoot ("lanes\" + $laneId + "\EXACT_OWNED_CLEANUP.json")
  if (-not (Test-Path -LiteralPath $cleanupPath -PathType Leaf)) { Fail "cleanup attestation missing after lane: $laneId" }
  Assert-NoReparseTree $cleanupPath $WorkRoot
  $cleanup = Get-Content -LiteralPath $cleanupPath -Raw -Encoding UTF8 | ConvertFrom-Json
  if ($cleanup.schema -ne "olm_exact_owned_cleanup_v2_20260730" -or
      $cleanup.lane_id -cne $laneId -or
      $cleanup.request_manifest_sha256 -cne $requestManifestHash -or
      $cleanup.prepared_state_sha256 -cne $preparedHash -or
      $cleanup.identity_revalidated -ne $true -or
      $cleanup.cleanup_complete -ne $true -or
      $cleanup.unrelated_processes_touched -ne $false) {
    Fail "exact-owned cleanup did not validate; refusing to start the next lane"
  }
  Assert-NoAfterFX
  $results += [pscustomobject]@{
    lane=$laneId
    terminal=$(if ($code -eq 0) { "candidate_answered_requires_return_validation" } else { "exact_bind_failure" })
    exit_code=$code
    reason=$(if ($code -eq 0) { "validate complete raw same-run contract" } else { "lane runner failed closed" })
  }
}
$results | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $WorkRoot "BATCH_EXECUTION_STATUS_20260730.json") -Encoding UTF8
Write-Host "ALL_LANES_TERMINAL_OR_CANDIDATE. Assemble ONE return ZIP and validate it with this entrypoint."
'''


def return_validator(request_manifest_sha256: str, return_contract_sha256: str) -> bytes:
    source = r'''#!/usr/bin/env python3
import hashlib, io, json, re, struct, sys, zipfile, zlib
from pathlib import PurePosixPath

EXPECTED_REQUEST_MANIFEST_SHA256 = "__REQUEST_MANIFEST_SHA256__"
EXPECTED_RETURN_CONTRACT_SHA256 = "__RETURN_CONTRACT_SHA256__"

def die(message): raise SystemExit("FAIL_CLOSED: " + message)
def strict_json(data, label):
    if data.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff", b"\xff\xfe\x00\x00", b"\x00\x00\xfe\xff")):
        die("BOM/UTF-16/UTF-32 forbidden: " + label)
    try: text=data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as e: die("strict UTF-8 required for "+label+": "+str(e))
    def reject(value): die("non-finite/duplicate-invalid JSON constant in "+label+": "+value)
    try: return json.loads(text, parse_constant=reject, object_pairs_hook=lambda p: unique_object(p,label))
    except (json.JSONDecodeError, TypeError) as e: die("invalid JSON "+label+": "+str(e))
def unique_object(pairs,label):
    out={}
    for key,value in pairs:
        if key in out: die("duplicate JSON key in "+label+": "+key)
        out[key]=value
    return out
def require_keys(obj, keys, label):
    if not isinstance(obj,dict) or not keys <= set(obj): die("missing fields in "+label)
def evidence_json(item, expected_schema):
    obj=strict_json(members[item["path"]], item["path"])
    if obj.get("schema") != expected_schema: die("evidence schema mismatch: "+item["path"])
    return obj
def canonical_zip_bytes(member_map):
    sink=io.BytesIO()
    with zipfile.ZipFile(sink,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as out:
        for name in sorted(member_map):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
            info.create_system=3
            info.external_attr=0o100644<<16
            info.compress_type=zipfile.ZIP_DEFLATED
            info.extra=b""; info.comment=b""
            out.writestr(info,member_map[name],compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    return sink.getvalue()
def parse_png(data,label):
    if not data.startswith(b"\x89PNG\r\n\x1a\n"): die("required PNG signature missing: "+label)
    pos=8; chunks=[]; idat=[]; ihdr=None; saw_iend=False
    while pos < len(data):
        if pos+12 > len(data): die("truncated PNG chunk: "+label)
        length=struct.unpack(">I",data[pos:pos+4])[0]
        ctype=data[pos+4:pos+8]; start=pos+8; end=start+length
        if end+4 > len(data): die("truncated PNG payload: "+label)
        payload=data[start:end]; crc=struct.unpack(">I",data[end:end+4])[0]
        if (zlib.crc32(ctype+payload)&0xffffffff) != crc: die("PNG CRC mismatch: "+label)
        chunks.append(ctype)
        if ctype==b"IHDR":
            if ihdr is not None or length!=13: die("invalid PNG IHDR: "+label)
            ihdr=struct.unpack(">IIBBBBB",payload)
        elif ctype==b"IDAT": idat.append(payload)
        elif ctype==b"IEND":
            if length!=0: die("invalid PNG IEND: "+label)
            saw_iend=True; pos=end+4
            if pos!=len(data): die("trailing PNG bytes forbidden: "+label)
            break
        pos=end+4
    if ihdr is None or not idat or not saw_iend or chunks[0]!=b"IHDR" or chunks[-1]!=b"IEND": die("incomplete PNG: "+label)
    width,height,depth,color,compression,filter_method,interlace=ihdr
    channels={0:1,2:3,4:2,6:4}.get(color)
    if not width or not height or channels is None or depth not in (8,16) or compression or filter_method or interlace: die("unsupported/noncanonical PNG format: "+label)
    bpp=channels*(depth//8); stride=width*bpp
    try: packed=zlib.decompress(b"".join(idat))
    except zlib.error as e: die("PNG inflate failure "+label+": "+str(e))
    if len(packed)!=height*(stride+1): die("PNG dimensions/payload mismatch: "+label)
    rows=[]; prior=bytearray(stride); cursor=0
    for _ in range(height):
        f=packed[cursor]; cursor+=1; scan=bytearray(packed[cursor:cursor+stride]); cursor+=stride
        if f>4: die("invalid PNG filter: "+label)
        for x in range(stride):
            left=scan[x-bpp] if x>=bpp else 0; up=prior[x]; ul=prior[x-bpp] if x>=bpp else 0
            if f==1: scan[x]=(scan[x]+left)&255
            elif f==2: scan[x]=(scan[x]+up)&255
            elif f==3: scan[x]=(scan[x]+((left+up)//2))&255
            elif f==4:
                p=left+up-ul; pa=abs(p-left); pb=abs(p-up); pc=abs(p-ul)
                pr=left if pa<=pb and pa<=pc else up if pb<=pc else ul
                scan[x]=(scan[x]+pr)&255
        rows.append(bytes(scan)); prior=scan
    pixels=b"".join(rows)
    return {"width":width,"height":height,"bit_depth":depth,"color_type":color,"pixels":pixels}
path = sys.argv[1]
try: archive_bytes=open(path,"rb").read()
except OSError as e: die("cannot read return ZIP: "+str(e))
try:
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        if any(i.is_dir() for i in z.infolist()): die("directory member forbidden")
        infos=z.infolist(); names=[i.filename for i in infos]
        if names != sorted(names): die("return ZIP member order is not canonical")
        for i in infos:
            if i.date_time != (1980,1,1,0,0,0): die("return ZIP timestamp is not canonical")
            if i.create_system != 3 or i.compress_type != zipfile.ZIP_DEFLATED: die("return ZIP system/compression metadata is not canonical")
            mode=i.external_attr>>16
            if (mode & 0o170000) != 0o100000 or (mode & 0o777) != 0o644: die("return ZIP file mode/type is not canonical")
        if len(names) != len(set(n.casefold() for n in names)): die("duplicate Windows member")
        if any("\\" in n or n.startswith("/") or ".." in PurePosixPath(n).parts for n in names): die("unsafe member")
        members = {n: z.read(n) for n in names}
except (zipfile.BadZipFile, OSError) as e: die("invalid ZIP: " + str(e))
if canonical_zip_bytes(members) != archive_bytes: die("return ZIP is not byte-canonical; use bundled canonical packager")
required = {"RETURN_MANIFEST.json","REQUEST_MANIFEST.json","RETURN_CONTRACT.json","CHECKSUMS.sha256"}
if not required <= set(members): die("missing fixed member")
try: checks = members["CHECKSUMS.sha256"].decode("ascii")
except UnicodeDecodeError: die("checksums not ASCII")
if not checks.endswith("\n"): die("checksums missing final LF")
rows = []
for line in checks.splitlines():
    m = re.fullmatch(r"([0-9a-f]{64})  ([^\r\n]+)", line)
    if not m: die("malformed checksum row")
    rows.append((m.group(2),m.group(1)))
expected = sorted(n for n in members if n != "CHECKSUMS.sha256")
if [n for n,_ in rows] != expected: die("checksum inventory/order not canonical")
for n,h in rows:
    if hashlib.sha256(members[n]).hexdigest() != h: die("checksum mismatch: " + n)
if hashlib.sha256(members["REQUEST_MANIFEST.json"]).hexdigest() != EXPECTED_REQUEST_MANIFEST_SHA256:
    die("immutable request manifest binding mismatch")
if hashlib.sha256(members["RETURN_CONTRACT.json"]).hexdigest() != EXPECTED_RETURN_CONTRACT_SHA256:
    die("immutable return contract binding mismatch")
ret=strict_json(members["RETURN_MANIFEST.json"],"RETURN_MANIFEST.json")
req=strict_json(members["REQUEST_MANIFEST.json"],"REQUEST_MANIFEST.json")
contract=strict_json(members["RETURN_CONTRACT.json"],"RETURN_CONTRACT.json")
if ret.get("schema") != "olm_windows_owner_retry_return_v2_20260730": die("return schema mismatch")
if req.get("schema") != "olm_windows_owner_retry_request_v2_20260730": die("request schema mismatch")
if contract.get("schema") != "olm_windows_owner_retry_return_contract_v2_20260730": die("contract schema mismatch")
lanes=ret.get("lanes")
if not isinstance(lanes,list) or [x.get("id") for x in lanes] != [
 "radial_cleanup_20260730_v2","directional_store_render_20260730_v2","dg_raw_typed_coordinate_20260730_v2"
]: die("all three lanes required in order")
seen_paths=set()
for lane in lanes:
    if lane.get("status") not in ("answered","exact_bind_failure"): die("invalid lane status")
    evidence=lane.get("evidence")
    if not isinstance(evidence,list) or not evidence: die("lane evidence required")
    root="lanes/"+lane["id"]+"/"
    by_kind={}
    for item in evidence:
        require_keys(item,{"path","sha256","kind"},"evidence record")
        n=item.get("path","")
        if not n.startswith(root) or n not in members or n.lower().endswith(".zip"): die("invalid direct evidence path")
        if members[n].startswith((b"PK\x03\x04",b"PK\x05\x06",b"PK\x07\x08")): die("ZIP payload forbidden as evidence")
        if not members[n]: die("empty evidence forbidden")
        if hashlib.sha256(members[n]).hexdigest()!=item.get("sha256"): die("evidence hash mismatch")
        if n in seen_paths: die("evidence path referenced more than once: "+n)
        seen_paths.add(n)
        if item["kind"] in by_kind: die("duplicate evidence kind: "+item["kind"])
        by_kind[item["kind"]]=item
    common={
      "binding_json":"olm_same_run_binding_v2_20260730",
      "process_identity_json":"olm_exact_owned_process_v2_20260730",
      "module_identity_json":"olm_loaded_aex_identity_v2_20260730",
      "no_effect_image":None,
      "effect_image":None,
      "raw_image_comparison_json":"olm_raw_image_comparison_v2_20260730",
      "cleanup_json":"olm_exact_owned_cleanup_v2_20260730",
    }
    if not set(common) <= set(by_kind): die("missing common raw same-run evidence kinds")
    binding=evidence_json(by_kind["binding_json"],common["binding_json"])
    binding_keys={"request_manifest_sha256","run_id","project_sha256","case_id","afterfx_pid","afterfx_creation_time","aex_path","aex_sha256","aex_base","renderer","bit_depth","source_sha256"}
    require_keys(binding,binding_keys,"same-run binding")
    if binding["request_manifest_sha256"] != EXPECTED_REQUEST_MANIFEST_SHA256: die("request binding mismatch")
    for key in ("run_id","case_id","afterfx_creation_time","aex_path","aex_base","renderer"):
        if not isinstance(binding[key],str) or not binding[key]: die("empty/invalid binding field: "+key)
    for key in ("project_sha256","aex_sha256","source_sha256"):
        if not isinstance(binding[key],str) or not re.fullmatch(r"[0-9a-f]{64}",binding[key]): die("invalid bound SHA-256: "+key)
    if not isinstance(binding["afterfx_pid"],int) or binding["afterfx_pid"] <= 0: die("invalid bound AfterFX PID")
    if binding["bit_depth"] not in (8,16,32): die("invalid bound bit depth")
    for kind,schema in common.items():
        if schema and kind != "binding_json":
            obj=evidence_json(by_kind[kind],schema)
            if kind != "raw_image_comparison_json":
                if obj.get("binding") != binding: die("cross-artifact binding mismatch: "+kind)
    process=evidence_json(by_kind["process_identity_json"],common["process_identity_json"])
    require_keys(process,{"binding","executable_path","command_line","parent_pid","run_nonce"},"process identity")
    if not all(isinstance(process[k],str) and process[k] for k in ("executable_path","command_line","run_nonce")): die("incomplete process identity")
    if not isinstance(process["parent_pid"],int) or process["parent_pid"] <= 0: die("invalid parent PID")
    module=evidence_json(by_kind["module_identity_json"],common["module_identity_json"])
    require_keys(module,{"binding","installed_path","loaded_path","loaded_sha256","loaded_base"},"module identity")
    if module["loaded_path"] != binding["aex_path"] or module["loaded_sha256"] != binding["aex_sha256"] or module["loaded_base"] != binding["aex_base"]: die("module/binding mismatch")
    cleanup=evidence_json(by_kind["cleanup_json"],common["cleanup_json"])
    if cleanup.get("identity_revalidated") is not True or cleanup.get("cleanup_complete") is not True or cleanup.get("unrelated_processes_touched") is not False: die("cleanup did not fail closed")
    compare=evidence_json(by_kind["raw_image_comparison_json"],common["raw_image_comparison_json"])
    no_item,fx_item=by_kind["no_effect_image"],by_kind["effect_image"]
    if no_item["path"]==fx_item["path"] or no_item["sha256"]==fx_item["sha256"]: die("control/effect artifacts must be distinct")
    control=parse_png(members[no_item["path"]],no_item["path"]); effect=parse_png(members[fx_item["path"]],fx_item["path"])
    if (control["width"],control["height"],control["bit_depth"],control["color_type"]) != (effect["width"],effect["height"],effect["bit_depth"],effect["color_type"]): die("control/effect PNG format or dimensions differ")
    different_bytes=sum(a!=b for a,b in zip(control["pixels"],effect["pixels"]))
    metrics={
      "width":control["width"],"height":control["height"],"bit_depth":control["bit_depth"],"color_type":control["color_type"],
      "decoded_byte_count":len(control["pixels"]),"different_byte_count":different_bytes,
      "control_pixel_sha256":hashlib.sha256(control["pixels"]).hexdigest(),
      "effect_pixel_sha256":hashlib.sha256(effect["pixels"]).hexdigest(),
    }
    if compare.get("binding") != binding or compare.get("no_effect_sha256") != no_item["sha256"] or compare.get("effect_sha256") != fx_item["sha256"] or compare.get("raw_comparison_performed") is not True or compare.get("metrics") != metrics: die("raw image comparison binding/metrics mismatch")
    lane_raw={
      "radial_cleanup_20260730_v2":("radial_raw_sampler_json","olm_radial_raw_sampler_v2_20260730",{"coordinates","sampler_words","cdb_detached"}),
      "directional_store_render_20260730_v2":("directional_raw_store_json","olm_directional_raw_store_v2_20260730",{"coordinate","writer_rva","target_address","pre_bytes","post_bytes","thread_id","breakpoint_slot"}),
      "dg_raw_typed_coordinate_20260730_v2":("dg_raw_entry_json","olm_dg_raw_entry_v2_20260730",{"rip","rcx","rdx","r8","r9","rsp_20","rsp_28","rsp_30","stack_trace","disassembly","address_info","lmvm","raw_entry_hit_count"}),
    }[lane["id"]]
    if lane_raw[0] not in by_kind: die("missing lane raw evidence")
    raw=evidence_json(by_kind[lane_raw[0]],lane_raw[1])
    require_keys(raw,{"binding"}|lane_raw[2],"lane raw evidence")
    if raw["binding"] != binding: die("lane raw binding mismatch")
    if lane["id"]=="radial_cleanup_20260730_v2":
        if raw["cdb_detached"] is not True or not isinstance(raw["coordinates"],list) or not raw["coordinates"] or not isinstance(raw["sampler_words"],list) or not raw["sampler_words"]: die("invalid radial raw sampler evidence")
    if lane["id"]=="directional_store_render_20260730_v2":
        if raw["coordinate"] != [494,169] or not all(isinstance(raw[k],str) and raw[k] for k in ("writer_rva","target_address","pre_bytes","post_bytes","thread_id","breakpoint_slot")): die("invalid directional raw store evidence")
        if raw["pre_bytes"] == raw["post_bytes"]: die("directional store did not change raw bytes")
    if lane["id"]=="dg_raw_typed_coordinate_20260730_v2":
        if "dg_typed_coordinate_json" not in by_kind: die("missing DG typed-coordinate evidence")
        typed=evidence_json(by_kind["dg_typed_coordinate_json"],"olm_dg_typed_coordinate_v2_20260730")
        require_keys(typed,{"binding","typed_hit_count","coordinate_contract"},"DG typed evidence")
        if typed["binding"] != binding: die("DG typed binding mismatch")
        if not isinstance(raw["raw_entry_hit_count"],int) or raw["raw_entry_hit_count"] < 0 or not isinstance(typed["typed_hit_count"],int) or typed["typed_hit_count"] < 0: die("invalid DG hit counts")
    referenced={item["path"] for row in lanes for item in row.get("evidence",[])}
    claims=lane.get("claims",{})
    if claims.get("cli_exact") is True and claims.get("ae_exact") is True: die("CLI exact never substitutes for AE exact")
    if lane.get("status")=="answered":
        if lane["id"]=="dg_raw_typed_coordinate_20260730_v2" and (raw["raw_entry_hit_count"] <= 0 or typed["typed_hit_count"] <= 0): die("answered DG lane lacks raw+typed hits")
        if claims.get("ae_exact") is True and different_bytes <= 0: die("AE exact requires recomputed effect/control raw difference")
fixed={"RETURN_MANIFEST.json","REQUEST_MANIFEST.json","RETURN_CONTRACT.json","CHECKSUMS.sha256"}
if set(members)-fixed != referenced: die("unexpected, unreferenced, or multiply claimed return member")
print(json.dumps({"status":"accepted","sha256":hashlib.sha256(archive_bytes).hexdigest()},sort_keys=True))
'''
    return (
        source.replace("__REQUEST_MANIFEST_SHA256__", request_manifest_sha256)
        .replace("__RETURN_CONTRACT_SHA256__", return_contract_sha256)
        .encode("ascii")
    )


def return_packager() -> bytes:
    return b'''#!/usr/bin/env python3
"""Create the one byte-canonical Windows owner retry return ZIP."""
import hashlib, io, os, sys, zipfile
from pathlib import Path

def die(message): raise SystemExit("FAIL_CLOSED: "+message)
if len(sys.argv)!=3: die("usage: pack_windows_owner_retry_return_v2_20260730.py STAGE_DIR RETURN.zip")
root=Path(sys.argv[1]).resolve(); output=Path(sys.argv[2]).resolve()
if not root.is_dir(): die("stage directory missing")
members={}
for path in sorted(root.rglob("*")):
    if path.is_symlink(): die("symlink/reparse-like stage entry forbidden: "+str(path))
    if path.is_dir(): continue
    try: path.resolve().relative_to(root)
    except ValueError: die("stage entry resolves outside root: "+str(path))
    name=path.relative_to(root).as_posix()
    if name=="CHECKSUMS.sha256": continue
    if not name or name.startswith("/") or ".." in Path(name).parts or "\\\\" in name: die("unsafe member: "+name)
    if name.casefold() in {n.casefold() for n in members}: die("duplicate Windows member: "+name)
    members[name]=path.read_bytes()
members["CHECKSUMS.sha256"]="".join(
    hashlib.sha256(members[name]).hexdigest()+"  "+name+"\\n" for name in sorted(members)
).encode("ascii")
sink=io.BytesIO()
with zipfile.ZipFile(sink,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
    for name in sorted(members):
        info=zipfile.ZipInfo(name,(1980,1,1,0,0,0))
        info.create_system=3
        info.external_attr=0o100644<<16
        info.compress_type=zipfile.ZIP_DEFLATED
        info.extra=b""; info.comment=b""
        archive.writestr(info,members[name],compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
output.parent.mkdir(parents=True,exist_ok=True)
temporary=output.with_name(output.name+".tmp")
temporary.write_bytes(sink.getvalue())
os.replace(temporary,output)
print(hashlib.sha256(output.read_bytes()).hexdigest()+"  "+str(output))
'''


def build(original: Path, output: Path) -> dict[str, object]:
    original_bytes = original.read_bytes()
    validate_original(original_bytes)
    lanes = [
        {
            "id": "radial_cleanup_20260730_v2",
            "purpose": "repair exact-owned cleanup and retain complete same-run radial raw evidence",
            "original_child_package": "jobs/001_olmradialblur_case0010_upstream_sampler_20260728_r3/package.zip",
            "original_child_sha256": "6a8d9404e60de3656877aa55ca97546c5fa1f4cab33c50e9a9fc9984b5781774",
        },
        {
            "id": "directional_store_render_20260730_v2",
            "purpose": "bind raw target store to no-effect/effect renders from the same owned AE run",
            "original_child_package": "jobs/002_olmdirectionalblur_target_writer_20260728_r3/package.zip",
            "original_child_sha256": "42226b5764fbf3618102f2c91feea2cbcd412a5317f85454446f03ba4590e5a4",
        },
        {
            "id": "dg_raw_typed_coordinate_20260730_v2",
            "purpose": "diagnose raw entry arguments and repair the typed-coordinate contract",
            "original_child_package": "jobs/003_olmdistancegradation_pf16_boundary_20260728_r2/package.zip",
            "original_child_sha256": "8e931aa7bc8a7a67829c6c5b4c94ac8cdfeac10599690d0e7891a429c0985027",
        },
    ]
    manifest = {
        "schema": REQUEST_SCHEMA,
        "request_id": "olm_windows_owner_retry_20260730_v2",
        "date": "2026-07-30",
        "start_gate": "HOLD",
        "entrypoint": ENTRYPOINT,
        "single_consolidated_return_only": True,
        "original_r1": {"member": ORIGINAL_NAME, "sha256": ORIGINAL_SHA256, "immutable": True},
        "rejected_return": {
            "filename": "OLM_WINDOWS_OWNER_RETRY_RETURN_20260730.zip",
            "sha256": REJECTED_RETURN_SHA256,
            "embedded": False,
            "admissible": False,
            "reason": "canonical parent checksum inventory validation failed",
        },
        "lanes": lanes,
    }
    contract = {
        "schema": "olm_windows_owner_retry_return_contract_v2_20260730",
        "return_schema": RETURN_SCHEMA,
        "archive_count": 1,
        "all_lanes_required": [lane["id"] for lane in lanes],
        "terminal_statuses": ["answered", "exact_bind_failure"],
        "canonical_checksums": {
            "member": "CHECKSUMS.sha256",
            "coverage": "every other member exactly once",
            "order": "lexicographic_by_exact_member_name",
            "validate_before_delivery": True,
        },
        "canonical_zip": {
            "member_order": "lexicographic_exact_name",
            "timestamp": "1980-01-01T00:00:00",
            "compression": "deflate",
            "create_system": "unix",
            "regular_file_mode": "0644",
            "archive_comment": "empty",
            "entry_comments": "empty",
            "entry_extra_fields": "empty",
            "flags_attributes_versions": "exact_bundled_packager_output",
            "validator_enforced": True,
            "byte_for_byte_reconstruction_required": True,
            "packager": RETURN_PACKAGER,
        },
        "lane_evidence_schemas": {
            "common": [
                "olm_same_run_binding_v2_20260730",
                "olm_exact_owned_process_v2_20260730",
                "olm_loaded_aex_identity_v2_20260730",
                "olm_raw_image_comparison_v2_20260730",
                "olm_exact_owned_cleanup_v2_20260730",
            ],
            "radial_cleanup_20260730_v2": "olm_radial_raw_sampler_v2_20260730",
            "directional_store_render_20260730_v2": "olm_directional_raw_store_v2_20260730",
            "dg_raw_typed_coordinate_20260730_v2": [
                "olm_dg_raw_entry_v2_20260730",
                "olm_dg_typed_coordinate_v2_20260730",
            ],
        },
        "answered_gates": [
            "same_run_raw_runtime",
            "exact_owned_process",
            "no_effect_control",
            "effect_output",
            "raw_image_comparison",
            "cleanup_fail_closed",
        ],
        "claim_limits": {
            "cli_exact_substitutes_ae_exact": False,
            "ae_exact_requires_all_answered_gates": True,
            "whole_plugin_claim": False,
        },
    }
    request_manifest_bytes = canonical_json(manifest)
    return_contract_bytes = canonical_json(contract)
    members = {
        "README_FIRST.md": instructions(),
        "REQUEST_MANIFEST.json": request_manifest_bytes,
        "RETURN_CONTRACT.json": return_contract_bytes,
        ENTRYPOINT: entrypoint(),
        "validate_windows_owner_retry_return_v2_20260730.py": return_validator(
            sha256(request_manifest_bytes), sha256(return_contract_bytes)
        ),
        RETURN_PACKAGER: return_packager(),
        ORIGINAL_NAME: original_bytes,
    }
    members["CHECKSUMS.sha256"] = "".join(
        f"{sha256(members[name])}  {name}\n" for name in sorted(members)
    ).encode("ascii")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(members):
            info = zipfile.ZipInfo(name, ZIP_EPOCH)
            info.create_system = 3
            info.external_attr = ((0o755 if name.endswith((".ps1", ".py")) else 0o644) | stat.S_IFREG) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, members[name])
    validate_request(output)
    return {"output": str(output), "sha256": sha256(output.read_bytes()), "members": len(members)}


def validate_request(path: Path) -> dict[str, object]:
    members = read_zip(path)
    validate_checksums(members)
    required = {
        "README_FIRST.md", "REQUEST_MANIFEST.json", "RETURN_CONTRACT.json",
        "CHECKSUMS.sha256", ENTRYPOINT,
        "validate_windows_owner_retry_return_v2_20260730.py", RETURN_PACKAGER, ORIGINAL_NAME,
    }
    if set(members) != required:
        raise ContractError("request member set mismatch")
    manifest = json.loads(members["REQUEST_MANIFEST.json"])
    contract = json.loads(members["RETURN_CONTRACT.json"])
    if manifest.get("schema") != REQUEST_SCHEMA or manifest.get("entrypoint") != ENTRYPOINT:
        raise ContractError("request manifest mismatch")
    if contract.get("return_schema") != RETURN_SCHEMA:
        raise ContractError("return contract mismatch")
    validate_original(members[ORIGINAL_NAME])
    return {"status": "accepted", "sha256": sha256(path.read_bytes()), "members": len(members)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate-request", type=Path)
    args = parser.parse_args()
    try:
        if args.validate_request:
            result = validate_request(args.validate_request)
        elif args.original and args.output:
            result = build(args.original, args.output)
        else:
            parser.error("use --original with --output, or --validate-request")
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
