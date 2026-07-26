param(
  [Parameter(Mandatory = $true)]
  [int]$ProcessId,

  [Parameter(Mandatory = $true)]
  [string]$AddressHex,

  [Parameter(Mandatory = $true)]
  [int]$Length,

  [Parameter(Mandatory = $true)]
  [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;

public static class NativeMemoryReader
{
    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr OpenProcess(
        uint processAccess,
        bool inheritHandle,
        int processId);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool ReadProcessMemory(
        IntPtr process,
        IntPtr baseAddress,
        byte[] buffer,
        UIntPtr size,
        out UIntPtr bytesRead);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(IntPtr handle);
}
'@

$processVmRead = [uint32]0x0010
$processQueryInformation = [uint32]0x0400
$access = $processVmRead -bor $processQueryInformation
$handle = [NativeMemoryReader]::OpenProcess($access, $false, $ProcessId)
if ($handle -eq [IntPtr]::Zero) {
  throw "OpenProcess failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
}

try {
  $address = [Convert]::ToUInt64($AddressHex, 16)
  $buffer = [byte[]]::new($Length)
  $bytesRead = [UIntPtr]::Zero
  $ok = [NativeMemoryReader]::ReadProcessMemory(
    $handle,
    [IntPtr]::new([int64]$address),
    $buffer,
    [UIntPtr]::new([uint64]$Length),
    [ref]$bytesRead)
  if (-not $ok) {
    throw "ReadProcessMemory failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
  }
  if ($bytesRead.ToUInt64() -ne [uint64]$Length) {
    throw "short read: $($bytesRead.ToUInt64()) of $Length"
  }

  [IO.File]::WriteAllBytes($OutputPath, $buffer)
  $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $OutputPath
  "READ_PROCESS_MEMORY pid=$ProcessId address=0x$AddressHex length=$Length"
  "SHA256=$($hash.Hash.ToLowerInvariant())"
} finally {
  [void][NativeMemoryReader]::CloseHandle($handle)
}
