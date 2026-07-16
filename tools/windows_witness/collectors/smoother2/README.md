# OLMSmoother2 Windows witness collector

This is a bounded, no-debugger, same-bitness x64 witness collector. The injector contract is:

```text
olm_injector.exe --pid <PID> --dll <absolute DLL> --config <absolute JSON>
```

The injector uses `OpenProcess`, `VirtualAllocEx`, `WriteProcessMemory`, and `CreateRemoteThread(LoadLibraryW)` to load the inert DLL. It then computes the local RVA of the exported `OLMInitializeCollector` with `LoadLibraryExW(DONT_RESOLVE_DLL_REFERENCES)` and `GetProcAddress`, finds exactly one matching remote module through a Toolhelp snapshot, and calls `remote_base + export_rva` with the original absolute config path. No debugger APIs, named objects, sidecars, or `DLL_PROCESS_ATTACH` worker startup are used, so an SSH injector in Session 0 can explicitly initialize an AE target in Session 1.

## Build

From an x64 Visual Studio developer prompt:

```powershell
cmake -S tools/windows_witness/collectors/smoother2 -B build/smoother2 -A x64
cmake --build build/smoother2 --config Release
```

Outputs are `olm_injector.exe` and `olm_smoother2_collector.dll`.

CMake is optional. On a Windows host without CMake, run:

```bat
tools\windows_witness\collectors\smoother2\build.cmd
```

`build.cmd` locates the latest x64 C++ Visual Studio installation with `vswhere`, falls back to `C:\Program Files\Microsoft Visual Studio\18\Community`, calls `vcvars64.bat`, and builds Release binaries under `tools\windows_witness\collectors\smoother2\out\`. It uses MSVC `/std:c++17 /EHsc /W4 /permissive- /O2 /MT` and stops on compiler or linker failure; `/WX` is deliberately not enabled.

## Config contract

All identity and target fields are required. The collector currently accepts only target `(91,841)` and the concrete current-AEX probe names/RVAs below. `return_rva` on an entry is the expected return address on the stack.

```json
{
  "run_id": "s2-run-0012",
  "ae_pid": 7312,
  "case_id": "legacy_case_0012_gamma5_red_blue_current_aex",
  "project_bpc": 8,
  "renderer": "Software",
  "module": "OLMSmoother2.aex",
  "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "output_dir": "C:/absolute/witness-output",
  "target_x": 91,
  "target_y": 841,
  "timeout_ms": 300000,
  "probes": [
    {"name": "writer_anchor", "rva": "0x350b"},
    {"name": "e170_entry", "rva": "0xe170", "return_rva": "0xf284"},
    {"name": "e170_return", "rva": "0xf284"},
    {"name": "f270_entry", "rva": "0xf270", "return_rva": "0xff5b"},
    {"name": "f270_return", "rva": "0xff5b"},
    {"name": "e3a0_entry", "rva": "0xe3a0", "return_rva": "0xff5b"},
    {"name": "e3a0_return0", "rva": "0xe3f4"},
    {"name": "e3a0_return1", "rva": "0xe420"}
  ]
}
```

## Two-phase output

After module identity/hash checks, address checks, VEH registration, and every INT3 is armed, the DLL writes `collector_status.json` with `status: "armed"`, `run_id`, `ae_pid`, `case_id`, `module_base`, and `aex_sha256`. It does not write `ok` at arm time. The writer anchor reads exactly dword `[RSP+0x34]` and `[RSP+0x38]`; only `(91,841)` binds the state machine.

The collector emits CDB-compatible flat key/value lines to `collector_trace.txt` using the checked-in prefixes and fields: `S2_PRODUCER_BIND`, `S2_PRODUCER_E170_ENTRY`, `S2_PRODUCER_E170_RETURN`, `S2_PRODUCER_F270_ENTRY`, `S2_PRODUCER_F270_RETURN`, `S2_PRODUCER_E3A0_ENTRY`, and `S2_PRODUCER_E3A0_RETURN`. It also appends a small raw `collector.jsonl` record.

The e170 entry computes:

```text
center = class_base + 841*class_stride + 91*4
prev   = class_base + 840*class_stride + 91*4
left   = class_base + 841*class_stride + 90*4 + 1
```

It reads `class_stride` as a 32-bit value, then reads the three contract bytes and four-byte neighborhoods. `center_class_bytes` starts at `center`, `prev_class_bytes` starts at `prev`, and `left_class_bytes` starts at the left pixel base before the `+1` channel offset; `left_b1` remains the byte at `left_pixel+1`. e170 return records the RAX low byte. f270 entry saves `producer_struct=RCX`; f270 return and the selected e3a0 return read dword `+0x130`, RGBA dwords `+0x40..+0x4c`, and weight dword `+0x50` from that saved structure.

Only the live ordered cardinality `bind -> f270 entry -> e170 entry -> e170 return -> e3a0 entry -> one e3a0 return -> f270 return` writes `status: "ok"` and hit counts. `e3a0` is reached by a tail jump, so its stack return address is the outer `f270` caller at `+0xff5b`; `+0xe3f4` and `+0xe420` are its internal return sites. Ordinary writer-anchor calls, entry calls with unrelated return addresses, return hits from other threads, and probes for stages that are not currently expected are ignored and re-armed. A matched-event memory read failure, concurrent breakpoint ownership conflict, queue overflow, patch/re-arm failure, impossible CAS race, hash mismatch, or timeout writes a non-ok failed status. The final accepted return is not re-armed, and `ok` waits until its original instruction has completed under single-step. On success the collector deliberately leaves the VEH and remaining probes installed until the one-case AE process exits; eager cleanup raced other render threads in the same patched code and caused a host crash.

Status publication uses a temporary file in `output_dir`, closes it, then replaces `collector_status.json` with `MoveFileExW(MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)`, so readers do not observe a partially written armed/ok transition. INT3 restoration is transactional on partial arm failure, and restore/re-arm paths flush the instruction cache.

`OLMInitializeCollector(void* config_path_wide)` is an x64 `WINAPI` export. It copies the supplied UTF-16 absolute path into DLL-owned bounded storage under SEH, rejects concurrent or repeated initialization, creates the existing worker, and returns `1` only when startup was accepted. The injector requires that exact exit code before reporting success. The worker reads the runner-owned JSON in place and does not delete or modify it; the config remains available as a return diagnostic and still binds `run_id`, `ae_pid`, `case_id`, and the configured AEX SHA-256.

Remote module identity is fail-closed. The requested DLL and each Toolhelp candidate are normalized through `GetFinalPathNameByHandleW`; canonical path, basename, and PE `SizeOfImage` must produce exactly one match. Zero, multiple, or size-ambiguous matches prevent the initialization call. A timeout leaves the corresponding remote path allocation intact because the remote thread may still be reading it.

The injector treats `WAIT_TIMEOUT` as failure and intentionally does not free the remote DLL-path allocation while the remote thread may still be active.

## Limitations

This is not a production debugger replacement. It requires exact RVAs for the exact loaded binary, compatible process and module-snapshot rights, readable canonical DLL/config paths, and a same-bitness x64 target. A loaded collector accepts initialization only once; after an accepted worker start, later initialization attempts are rejected even if the worker subsequently fails. VEH handlers must remain bounded and do not use locks or stream I/O; observations are passed through a fixed queue to the worker. Concurrent breakpoint ownership is fail-closed rather than merged. There is no host-independent VEH self-test: config/parser and live breakpoint behavior still require an MSVC Windows build and a controlled target process. The collector does not suspend all threads, disassemble overwritten instructions, recover from another VEH consuming an exception, or guarantee arbitrary code remains safe under one-byte patching.
