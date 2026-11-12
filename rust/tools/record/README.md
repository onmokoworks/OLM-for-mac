# Real-render native call recorder

`record.py capture` runs the original AEX through the existing headless
AEXCompat oracle route and records selected internal calls and typed imports.
`record.py replay` feeds one captured call to the unmodified **witness** host
and a named Rust adapter, comparing both with the recorded return and buffers.
All authored files and generated artifacts belong to `rust/tools/record/`.
No AEXCompat, witness, oracle, or production source changes are required.

## Mechanism and scope

This implements option **(b): Windows debug API software breakpoints**. The
controller starts the harness suspended with `DEBUG_PROCESS`, assigns it to
a private kill-on-close Job Object, then resumes it. Windows reports only
that process and its inherited debug descendants. There is no attach-to-PID
command, service, admin installation, external instrumentation package, DLL
injection, AE launch, or GUI. The original file is never copied or modified.

This was the least invasive available mechanism: AEXCompat already supplies
the real SmartFX/classic host lifecycle, suites and worlds. Reimplementing
those in a minimal host would introduce a second host whose behavior needs
qualification. Debug events expose the registers/memory without a target-side
logger, allocator or trampoline. A worker hook patch, option (c), was unnecessary.

At module load, breakpoints are installed at the selected RVAs and loader entry.
At loader entry, after import binding, selected normal IAT slots are resolved
to their actual provider addresses. The provider functions receive entry/return
breakpoints too. Import calls are admitted only when their immediate return
address lies in the selected AEX. Each record retains the import DLL/name/IAT
RVA and actual provider path/hash/RVA; an import RVA is relative to that provider,
not to the AEX. Missing explicitly requested imports are rejected before launch.

A return breakpoint is matched by **thread ID and entry RSP + 8**, supporting
nested/recursive calls and shared return sites. Other live threads are explicitly
suspended while a removed INT3 is single-stepped, then resumed after reinsertion.
Threads reported during that interval are also suspended. The thread-exit race
is handled by checking exit status/signaling and `ThreadIsTerminated`; an
unexplained inability to suspend fails the capture. Thread order is observed
under instrumentation, not claimed to be the uninstrumented scheduler's order.

The controller drains debug exit events, terminates its job, checks the job's
active count reaches zero, and waits on a separately retained process handle.
Normal completion, crash, timeout and controller errors use the same cleanup.
Process IDs/exits and `cleanup_verified` are retained, including failed runs.
No process-name kill or global process enumeration is used.

API grounding: Microsoft documents [DEBUG_PROCESS descendant inheritance](https://learn.microsoft.com/en-us/windows/desktop/Debug/process-functions-for-debugging),
[debug event suspension and continuation](https://learn.microsoft.com/en-us/windows/win32/debug/writing-the-debugger-s-main-loop),
[debug handle closure](https://learn.microsoft.com/windows/win32/api/debugapi/nf-debugapi-continuedebugevent),
and the [ThreadIsTerminated information class](https://microsoft.github.io/windows-docs-rs/doc/windows/Wdk/System/Threading/constant.ThreadIsTerminated.html).

## Build and reproduce

Requires Windows AMD64, 64-bit Python 3.11+, dependencies in `requirements.txt`,
the existing AEXCompat harness, Rust/MSVC and cached Cargo dependencies. The
adapter compiles the existing production Rust source files directly, with no
copied or retuned algorithms. Its `olm-math` dependency and combined artifacts
are **OLM-internal and must not be published standalone**. The optional native
adapter has its own Cargo workspace and lockfile; the outer package is only a
marker for the parent `tools/*` workspace glob.

Run from the repository root. The existing witness host must already be built
at `rust/tools/witness/target/release/witness-host.exe`.

```powershell
cargo build --manifest-path rust/tools/record/adapter/Cargo.toml --release --offline --locked --jobs 2
python rust/tools/record/demo.py --originals '../ghidra_windows_aex' --out rust/tools/record/runs/reproduce-new
```

The demo runs **one render at a time**, an uninstrumented control for each,
replays every recorded call, then runs the deliberately incorrect Gaussian
adapter. Output directories must be new. `--harness PATH` overrides the shared
harness. The demo fails if the real SmartFX selector was not dispatched.

Individual capture and replay:

```powershell
python rust/tools/record/record.py capture --module '../ghidra_windows_aex/OLMDirectionalBlur.aex' --profile rust/tools/record/profiles/directional.json --request rust/tools/record/profiles/directional-request.json --out rust/tools/record/runs/capture-new --max-calls 128 --max-bytes 16777216 --timeout 120
python rust/tools/record/record.py replay rust/tools/record/runs/capture-new/calls/000000/record.json --out rust/tools/record/runs/replay-new
python rust/tools/record/record.py replay rust/tools/record/runs/capture-new/calls/000000/record.json --adapter wrong.gaussian --out rust/tools/record/runs/wrong-new
```

Capture also accepts `--route smart8|smart16|smart32|classic8|classic16|classic32`,
`--width`, `--height`, `--seed`, and a normal oracle request JSON. Defaults are
Smart8, 11x7, seed 20261112, 128 calls, 16 MiB of snapshots and 120 seconds.
Input pixels come from `oracle.input_pixels`; omitted requests use
`oracle.make_request` with untouched defaults and downsample 1. Supplied request
JSON is passed through, including its host context. Current real qualification
below is **Smart8 only**, not all exposed routes.

Exit codes: capture 0 = successful render with completed records, 2 = failed or
incomplete evidence; replay 0 = all compared bytes exact, 1 = mismatch. Invalid
configuration/replay prerequisites raise an exception and exit nonzero. An empty
capture is never success. `unobserved` lists requested functions with no accepted
records. A budgeted capture can succeed with partial call coverage, explicitly
reported by `budget_closed`; it is not a complete call census.

## Profile and record contracts

Profiles require `schema_version:1`, the exact `module_sha256`, and `functions`.
Every function needs a name, RVA, positional Windows-x64 scalar argument types,
return type, optional adapter name, and optional per-function `max_calls`.
`imports` uses the same signature/buffer description, with a name and optional
case-insensitive import `dll`, instead of an RVA. Types are
`u8/u16/u32/u64/i8/i16/i32/i64/f32/f64/ptr`; `void` is return-only. No signature or
buffer length is guessed from machine code. There are at most 32 scalar arguments.

Example Gaussian output descriptor:

```json
{"arg":0,"size":{"mul":[{"arg":1},4]},"stride":4,"role":"output"}
```

Sizes/strides use nonnegative integers, integer-argument references, or nested
`mul` expressions. Negative signed lengths, floating sizes, and expressions over
256 MiB fail. Strides are descriptive byte strides; snapshots are contiguous
spans of exactly `size` bytes, including declared padding. Buffers are captured
before **and** after even when marked output, preserving no-write behavior.
`{"returned":true,"size":{"arg":0},"stride":1}` captures memory pointed to by
a pointer return after completion. The caller supplies its known lifetime/size.
Buffer descriptors describe flat memory, not embedded-pointer object graphs.

Every accepted call reserves both snapshots (only after for returned buffers)
before reading memory. The global byte budget counts snapshot payload bytes;
call count bounds JSON metadata. Whole calls are omitted on budget exhaustion,
never truncated into apparently replayable records. Exhausted hooks stop logging
and execute normally; the manifest records the reason, not a fabricated count
of subsequent unobserved calls. Maximum limits are 100,000 calls and 256 MiB.

Layout is deterministic:

```text
manifest.json                 identities, command, budgets, processes, render evidence
profile.json / request.json   exact submitted contracts
input.png / output.png        real render input/output
stdout.txt / stderr.txt       harness diagnostics
calls.jsonl                   records in entry sequence, including incomplete entries
calls/000000/record.json       one record, updated only after its matched return
calls/000000/buffer0.before.bin
calls/000000/buffer0.after.bin
error.txt                     traceback on controller failure
```

A record contains function/provider RVA and hash, exact little-endian argument
bit patterns, entry/return order, PID/TID, caller, MXCSR, buffer addresses,
sizes/strides/roles and hashes, typed return bits, and diagnostic RAX/XMM0.
Sequence numbering follows accepted entries; `entry_order`/`return_order` share
one counter so nesting is preserved. ASLR pointers/PIDs and multithread order
naturally vary across runs; deterministic filenames do not imply identical logs.
Unused return-register bits and void RAX are diagnostic, not compared outputs.

Replay verifies module and snapshot identities, merges overlapping input spans,
relocates pointer arguments, and refuses unresolved non-null pointers. It calls
the existing `witness.run` and `witness.run_owned` APIs. Independent calls are
replayed in fresh workers; module globals, TLS, host callbacks and earlier hidden
side effects are not synthesized. A named Rust adapter receives exact argument
bits and entry snapshots, and returns complete buffer/return bytes.

For pointer returns, a small DLL under `adapter/` is invoked by **witness**. It
uses witness's public native ABI bridge to call the original and copy one bounded
returned allocation into a witness-owned buffer before the child exits. Pointer
values themselves cannot match across address spaces: nullness, captured alias
relation, and returned bytes are compared instead. The raw original return address
is still recorded. The fixture qualifies an allocated returned buffer; arbitrary
free functions, destructors and embedded-pointer ownership are not inferred.

`comparison.json` retains each comparison, byte counts, hashes, first differing
byte, adapter identity, witness manifest hash and both cleanup results. Adding
a Rust function means adding a small named dispatch arm in `adapter/src/main.rs`.
The Kira adapter converts captured radians back to the public function's degree
argument and **asserts the lowered float32 bits are identical** before calling
the existing `trig::extent_sincos`. No numerical tolerance is used.

## Verified real run on this machine

2026-11-12, Windows build 26300, Python 3.11.9, Rust 1.88.0. Full local artifacts
are under ignored `runs/real-final/`; compact identities/results are retained in
[`evidence/real-final.json`](evidence/real-final.json).

Two **real AEXCompat Smart8 renders**, 11x7, seed 20261112. Directional request:
angle slot 1 components `[27]`, front 8/fade 3, back 5/fade 2. Kira request:
angle slot 40 components `[33]`, other parameters
untouched, including its inconsistent declared Gain default. Successful SmartFX
dispatch and host stage events are retained in both manifests.

| Original | Internal calls | Import calls | Exact replay into original and Rust |
| --- | --- | --- | --- |
| DirectionalBlur | 4 Gaussian (`0x1830`), 2 rotations (`0x1ec0`) | 8 expf, 2 cosf, 2 sinf | **18/18** |
| KiraKira | 4 extent-sincos (`0x132b2e0`, packed two-float return) | 8 powf | **12/12** |

The four Gaussian lengths, in call order, are 8, 5, 3, 2. Rotation snapshots preserve both
17x17 RGBA-float buffers, including destination initialization. Directional
captures **37,136 snapshot bytes**; together the 30 calls compare **18,680
output/return bytes per replay implementation**, with zero differing bytes.
Both rendered PNGs are sample-exact against uninstrumented controls. These two
controls bound observed instrumentation effects; they do not prove universal
timing transparency.

The deliberately wrong `wrong.gaussian` adapter flips one output bit. Its replay
exits **1**, reports `record/rust:buffer0` mismatch at **byte 0**, and the same
record still matches the original witness exactly. This is a test-only wrong
variant; no production source is changed.

Both originals have **no normal IPP DLL imports**. UCRT calls above were captured
from actual resolved providers. IPP-style typed import interception is exercised
with the synthetic `ippRecordFixture` DLL in tests, explicitly **not** an Intel
IPP real-render claim. Statically linked IPP functions can be selected by known
RVA like any other internal; this tool does not discover their signatures.

## Tests and limits

```powershell
python -m unittest discover -s rust/tools/record -p test_record.py -v
cargo fmt --manifest-path rust/tools/record/adapter/Cargo.toml --check
cargo clippy --manifest-path rust/tools/record/adapter/Cargo.toml --release --offline --jobs 2 -- -D warnings
```

Observed: **19 Python tests passed**, adapter formatting and strict Clippy passed.
Clippy allowances are scoped to included, unchanged production modules; the
adapter code itself remains checked. Native tests compile owned Rust fixtures
under ignored `target/test-fixtures/`, retain their failure/success artifacts,
and verify four concurrent callers, integer/floating register and stack arguments,
nested calls, provider imports, writable buffers, returned-buffer witness/Rust
replay, call/byte budgets, bad reads, identity/missing-import rejection, crash,
timeout, and descendant cleanup. Fixtures are test drivers, not AE hosts.

Only Windows AMD64 scalar ABI is supported. No vectorcall/YMM/ZMM ABI, automatic
aggregate lowering, delay imports, dynamically looked-up exports, transitive
import census, JIT/self-modifying code, callbacks/object graphs, SEH unwind recovery,
nonlocal returns, or asynchronous retained buffers. Tail calls and unusual entry
instructions that defeat single-step/return tracking are not qualified. Such
failures are incomplete/error evidence, not successful comparisons. Breakpoints
change timing and can interact with debugger detection; high-frequency functions
should have small per-hook budgets. Code pages are changed only in owned processes.

The actual loaded UCRT provider identity and MXCSR are retained. Rust adapters use
their existing FMA implementation; no claim covers alternative FMA dispatch,
rounding modes, errno/FP exception flags or a different CPU. The captured bits and
both native/Rust results agree on this machine. Native AE, macOS, ToonDilate,
and the other route/depth combinations were not tested by this job.
