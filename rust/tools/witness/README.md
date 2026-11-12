# Native AEX internal-function witness

Run original Windows x64 `.aex` functions by RVA in a disposable native child,
with typed JSON arguments, raw return registers, buffer dumps and optional IAT
traces. Python never loads the AEX. Only the worker's copy of its normal import
table is patched; the original file and other processes are untouched.

This package has its own empty `[workspace]` and lockfile. All new sources and
artifacts live under `rust/tools/witness/`; it does not change the parent
workspace. `target/`, `runs/` and Python caches are ignored.

## Build and run

Windows x64, Python 3.11+, Rust/MSVC and the Windows SDK are required. These
commands run from the repository root. The basic host only needs serde and
serde_json; there is no Unicorn, libffi, AE SDK or AE runtime dependency.

```powershell
cargo build --manifest-path rust/tools/witness/Cargo.toml --release --offline --jobs 2
python rust/tools/witness/witness.py rust/tools/witness/examples/gaussian.json --out rust/tools/witness/runs/example --timeout 10
```

The example locates the existing originals directory alongside this repository.
Edit `module` for a different installation. Relative module and buffer-file paths
are resolved against the **input JSON's directory**. Output directories must be
new. Use `--host PATH` to select another worker build. The CLI returns 0 for a
completed batch and 2 for a child failure/timeout; validation exceptions are
controller errors, not successful witnesses.

The example calls DirectionalBlur's Gaussian table builder with a 128-byte
output buffer and length 32. Inspect `call-000000-table.bin` as 32 little-endian
float32 words. `trace.jsonl` contains the first eight `expf` calls; the remaining
24 execute normally and are counted as dropped trace records.

## JSON contract

`schema_version` is 1. `module` identifies one AMD64 PE32+ DLL/AEX. `calls` is
an ordered batch sharing its module and buffers. Each call needs `rva`, `args`
and `return`, with an optional human-readable `label`. An RVA is relative to the
**loaded module base**, never an absolute Ghidra virtual address. For an image
based at `0x180000000`, `FUN_180001830` has RVA `0x1830`. Confirm both the binary
identity and function signature before reusing RVAs from another version.

Supported scalar types are `u8/u16/u32/u64`, `i8/i16/i32/i64`, `f32/f64` and
`ptr`; `void` is return-only. Each argument supplies exactly one of:

| Argument | Meaning |
| --- | --- |
| `{"type":"i32","value":-7}` | Signed integer |
| `{"type":"u64","value":"0xffffffffffffffff"}` | Exact 64-bit integer; strings avoid JSON consumer precision loss |
| `{"type":"f64","value":0.5}` | Numeric double |
| `{"type":"f32","bits":"0x7fc01234"}` | Exact IEEE word, including NaN, infinity and signed zero |
| `{"type":"ptr","buffer":"pixels","offset":16}` | Pointer to allocated buffer plus byte offset |
| `{"type":"ptr","value":0}` | Null pointer; nonzero raw pointers are also accepted at the caller's risk |

`bits` is a **numeric hexadecimal word**. Buffer `hex` and output `bits_le` are
**bytes in memory order**: float32 1.0 is `bits:"0x3f800000"` but
`hex:"0000803f"`. Integer range, argument count, file size, pointer relocation
bounds and total buffer budget are checked. Unknown JSON fields are rejected
by the worker.

Buffers have `size` in bytes, optional `fill` (0..255, default 0), and either a
`file` or `hex` initializer. Initial bytes may be shorter than `size`; remaining
bytes retain `fill`. Allocations are 16-byte aligned, with checked 64-byte
redzones and a total 256 MiB limit. Redzones detect nearby overwrites after a
call; they are not protected pages and do not detect arbitrary invalid reads.
Buffers persist between calls, and every buffer is dumped after each completed
call. Run separate specs for independent initial state.

Struct blobs use the same buffers. For example, a native `{void *data; uint64_t
length;}` with four bytes of data is represented by:

```json
"buffers": {
  "data": {"size": 4, "file": "input.bin"},
  "context": {
    "size": 16,
    "hex": "00000000000000000400000000000000",
    "pointers": [{"offset": 0, "buffer": "data", "addend": 0}]
  }
}
```

Pass `{"type":"ptr","buffer":"context"}`. Each `pointers` entry writes an
eight-byte address into the initialized blob. Small by-value aggregates can be
described as integer bits; larger aggregates, `this`, and hidden structure-return
pointers must be lowered explicitly according to the function's actual ABI.
The tool does not infer C/C++ layouts or supply AE suite objects/callbacks.

## Calling convention and tracing

The assembly bridge supports 0..32 positional scalar arguments. Positions 0..3
populate RCX/RDX/R8/R9 and XMM0..3 with the same bit slots; this also permits
Windows vararg register duplication when arguments have already been promoted
by the spec author. Arguments 4..31 occupy eight-byte stack slots after the
32-byte shadow space. RSP is aligned to 16 bytes at `CALL`. The bridge preserves
the nonvolatile register it uses and captures RAX plus all 128 bits of XMM0.
`return.bits_le` selects only the declared scalar width. The other register and
unused upper XMM lanes are diagnostic scratch, not additional defined returns.

`trace.math:true` patches matching normal imports for `expf`, `powf`, `sinf`,
`cosf`, `log2f`, `atan2f`, `sin`, `cos`, `exp`, `pow`, `atan2`, `log`, `log2`,
`sqrt`, `ceil`, `floor`, `tan`, `atan`, `fabs`, `fmod` and their listed float
variants (see `src/trace.rs`). Custom scalar imports require a signature:

```json
"trace": {
  "math": true,
  "budget": 1000,
  "imports": [
    {"name":"GetTickCount","args":[],"return":"u32"},
    {"name":"memcpy","args":["ptr","ptr","u64"],"return":"ptr"}
  ]
}
```

An optional `dll` restricts the import descriptor name, case-insensitively;
ordinal imports can be specified as `"name":"#123"`. Explicitly requested
imports must be found, or the batch fails before calling its functions. The
math convenience list is best-effort and only patches names present. Signature
errors can crash or corrupt the child. Pointer traces record addresses, not
automatically dereferenced memory.

The trace budget is **global across the batch**, defaults to 10,000 when a trace
object is present, and may be zero. It limits logging, not target execution.
After the budget is exhausted, calls still forward to the original import.
Each JSONL record has an entry sequence number, current batch call index, thread
ID, argument bytes and return bytes. Nested calls may complete out of sequence;
no writer lock is held across the original call. Records are flushed after each
return. Win32 last-error is preserved around logging. errno and floating-point
exception flags are not qualified as transparent tracing behavior.

`fma` accepts `auto` (default), `fma` or `no-fma`. After LoadLibrary initialization,
the child queries the system UCRT's `_get_FMA3_enable`, optionally sets its lane,
and reports the observed value, DLL path, CPU FMA support and MXCSR. The trace
inventory additionally resolves each IAT target's actual provider DLL and queries
that provider's FMA getter when exported. A null provider FMA means unknown.
The manifest hashes the system UCRT. This does not control a statically linked
CRT, a separate private CRT, or embedded math such as KiraKira's sin/cos kernel.

## Isolation and artifacts

The controller creates the worker suspended and assigns it to a private
kill-on-close Windows Job Object **before resuming it**. Normal completion,
timeout and controller exceptions all terminate the owned job, poll its active
process count to zero, and wait for the exact worker PID. This also cleans up
descendants left alive after the worker exits. Output goes to files so inherited
pipe handles cannot block cleanup. No global hook, injection, process-name kill,
background server, installation or original-binary copy is used.

The worker checks that it runs inside a job and suppresses ordinary Windows
fault dialogs. It loads dependencies with DLL-directory/default-directory
search flags. Module initialization and all native calls occur inside that
child. This is crash isolation, **not a security sandbox**: use trusted binaries;
loaded code still has the user's ordinary filesystem/network privileges.

Each run retains:

- `spec.json`: normalized absolute paths and exact submitted arguments.
- `manifest.json`: module hashes before/after, worker/spec/UCRT/input/output
  hashes, machine identity, classification, timeout, PID, exit status and cleanup.
- `process.json`: PID recorded before resume, then final status and cleanup,
  including when the controller encounters an exception.
- `result.json`: completed batch metadata, FMA profile, installed hooks, trace
  totals, typed returns and buffer filenames.
- `calls.jsonl`, `trace.jsonl`, `call-NNNNNN-NAME.bin`: completed calls and
  available traces/dumps survive a later crash. An interrupted call has no
  guaranteed result; absence of `result.json` is never treated as success.
- `stdout.txt`, `stderr.txt`: child diagnostics; native crashes retain their
  hexadecimal exit status, such as `0xc000001d` for the test's illegal instruction.

## Worked real run on this machine

The demo compiles the **existing Rust translation source files** directly into
an optional reference binary; no second implementation or tuned constants are
introduced. Its `olm-math` dependency and the combined reference artifact are
**OLM-internal and must not be published standalone**. This optional build needs
the repository's clang-cl setup for its vendored C math sources.

```powershell
cargo build --manifest-path rust/tools/witness/Cargo.toml --release --offline --features demo --jobs 2
python rust/tools/witness/demo.py --originals 'D:/Projects/01_Project/04_Tools/olm for mac/ghidra_windows_aex' --out rust/tools/witness/runs/real-20261112-final
```

Observed output on 2026-11-12, Rust 1.88.0, Python 3.11.9, Windows build 26300,
AMD64 Family 25 Model 33 Stepping 2:

```text
gaussian: 495 cases, 0 mismatches, child 0.407s, cleanup=True
sincos: 5643 cases, 0 mismatches, child 0.765s, cleanup=True
```

Those timings include native child lifetime and output I/O. They are not a
controlled speedup measurement against Unicorn. Full local artifacts are under
the ignored `runs/real-20261112-final/`; choose a new directory when repeating.

| Original function and grounding | Corpus and comparison |
| --- | --- |
| DirectionalBlur RVA `0x1830`, [Gaussian table IR](../../../notes/IR_OLMDirectionalBlur.md#Gaussian-Table) | 495 lengths, 0..4096, seed 20261112; **551,594 float32 words**, zero differing bits against `algorithm::gaussian`; UCRT FMA=1 |
| KiraKira RVA `0x132b2e0`, [existing F11 witness](../../../tools/emulation/probe_kirakira_sincos_F11.py) | 5,643 degree-derived inputs: -720..720, signed zero/tiny values, random finite magnitudes and neighbors of both range-reduction boundaries; zero differing bits against `trig::extent_sincos` |

Kira's helper returns two packed float32 words in XMM0. The demo uses `return:
"f64"` solely to capture the low eight bytes; it compares those bytes as sine
and cosine, never interprets them as a numeric double. No embedded CPU dispatcher
is patched: this run qualifies the machine's naturally initialized lane.

Binary identities and concatenated comparison digests:

| Artifact | SHA-256 |
| --- | --- |
| Original DirectionalBlur | `d3e5e4079a759d521dc7457ebf998487fe43b00f182a1e2f910b187936b6c06e` |
| Original KiraKira | `60997c0c52207c15844a46289435231fa6b0a885f63778404e02cea6e03899f7` |
| Witness host | `6c337c82b320659aac86690eeb529c71de6872fc84a0f58c4e206f19425353e5` |
| System UCRT | `dedb7611e1abc1ff3852dcac3d4c93a048d729e25b061973b9969f22698f14ca` |
| Gaussian native **and** Rust output | `1361b9ff55baac8cd7264e728c41fd686c4ee836a29ce2f4e7c8dc7fa6dc1b23` |
| Sin/cos native **and** Rust output | `eae29fdaf7701430343ab12948240967acf4caad775340d9630c10d18f7733c1` |

Both original files retained their hashes after execution. The machine reported
`_get_FMA3_enable() == 1`, CPU FMA available and MXCSR `0x1fa0`. DirectionalBlur's
`expf` IAT slot at `0xb0e0` resolved to `C:\WINDOWS\System32\ucrtbase.dll`, whose
own getter also returned 1. The real path made 551,594 traced import calls: 64
recorded, 551,530 forwarded after budget exhaustion. One record, with volatile
thread/address fields omitted here:

```json
{"sequence":2,"call_index":2,"name":"expf","args_bits_le":["95ff8fbf"],"result":{"bits_le":"6439a63e"}}
```

This is the second weight for length 2, collected from the real native builder.
The full journal preserves RAX, XMM0, DLL name and thread ID as well.

## Verification and limits

```powershell
cargo test --manifest-path rust/tools/witness/Cargo.toml --release --offline --jobs 2
cargo fmt --manifest-path rust/tools/witness/Cargo.toml --check
cargo clippy --manifest-path rust/tools/witness/Cargo.toml --release --offline --jobs 2 -- -D warnings
Push-Location rust/tools/witness
python -m unittest -v test_witness
Pop-Location
```

Observed: **2 Rust tests and 18 Python tests passed**; host formatting and strict
Clippy passed. The Rust tests exercise 1,000 mixed register/stack cases, integer
and double returns, 16-byte stack alignment, writable shadow space, and argument
32. Python compiles small owned fixture DLLs and verifies custom mixed-argument
IAT forwarding, float/double math traces, budget exhaustion without result
changes, GetTickCount tracing, file buffers, struct relocations, redzone errors,
FMA=0 selection, missing imports, crash/timeout isolation, descendant cleanup,
and preservation of completed calls before a later crash. Fixture artifacts
remain under ignored `target/test-fixtures/`; temporary per-test runs are removed.

The entry points and all traced signatures must use the normal Windows x64
scalar ABI. There is no automatic `__vectorcall`, YMM/ZMM argument, C++ object,
exception-unwind, callback, AE suite, or variadic-promotion synthesis. Assembly
thunks have no Windows unwind metadata; exceptions escaping a called function
are unsupported and may terminate the child. No delay-load IAT, dynamically
resolved GetProcAddress calls, transitive DLL IAT, or statically embedded calls
are intercepted. LoadLibrary/DllMain runs before hooks are installed. Asynchronous
functions retaining buffer pointers after return are outside the lifetime
contract. There is a wall-clock timeout, not an instruction counter.

These are internal-function witnesses, not whole-render or native-AE acceptance.
Use [AEXCompat oracle](../oracle/README.md) for parameter transport, host suites,
pixel formats and complete CPU renders. Use [emulation](../../../tools/emulation/README.md)
on non-Windows systems and for instruction hooks, register checkpoints, controlled
memory faults and alternate CPU dispatch paths. Native execution supplies the
real Windows loader, TLS, CPU and installed UCRT behavior for small focused
experiments, while the other tools cover the broader render and inspection work.
