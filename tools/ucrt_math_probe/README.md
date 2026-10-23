# F27: direct UCRT math feasibility probe

**Blocked at FMA execution; this is not a completed libm comparison.**
No plugin, AEXCompat, oracle, release gate, or production math is changed.

## Reproduce on the Mac

Run from this worktree. Python dependencies are the existing MAIN venv's
`unicorn==2.1.4`, `pefile`, and `capstone==5.0.7`; MAIN is read-only.

```sh
PROBE_PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p orchestra/state/F27-ucrt-math-probe
"$PROBE_PY" tools/ucrt_math_probe/acquire.py > orchestra/state/F27-ucrt-math-probe/acquire.log
"$PROBE_PY" tools/ucrt_math_probe/probe.py --check tools/ucrt_math_probe/smoke_summary.json
```

Expected: `PASS: 30 smoke observations reproduce; status remains blocked`.
The command checks reproduction of failures as well as outputs; it is **not** a
math-correctness PASS. To regenerate the summary:

```sh
"$PROBE_PY" tools/ucrt_math_probe/probe.py > orchestra/state/F27-ucrt-math-probe/recheck.json
```

Acquisition uses Microsoft's official `Microsoft.Windows.SDK.CPP` NuGet package
10.0.28000.2705, containing
`c/Redist/10.0.28000.0/ucrt/DLLs/x64/ucrtbase.dll`. Package and DLL stay exclusively
in `~/.cache/olm-emu/ucrt/10.0.28000.2705/`. No Microsoft binaries are committed.
This package has no `libucrt.lib` member. This does not establish that the static
library is absent from other SDK packages. Binary identity:

- File version: `10.0.28000.2705`
- DLL SHA256: `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`

## What the probe does

Maps the PE at its preferred image base, resolves exports from the PE export
table, supplies a Win64 stack (entry RSP modulo 16 is 8 and shadow space exists),
and passes raw float bits in XMM0/XMM1. MXCSR starts at `0x1f80` (nearest-even,
FTZ/DAZ off). Calls are limited to 100,000 instructions and must reach the return
sentinel. Each observation uses a fresh machine. No math calls are replaced.
DLL startup, imports, TLS, errno, and exception handling are not implemented;
unmapped accesses fail rather than receiving invented results. Thus this is a
leaf smoke harness, **not yet a safe arbitrary-input oracle**.

The binary's `_set_FMA3_enable` at RVA `0xd6800` reads the capability mask at
`0x13bdf4` and writes the active mask at `0x13bdf0`. Calling it on an uninitialized
DLL does not enable FMA. The probe explicitly supplies capability mask 3 before
calling the real setter, and asserts the active mask becomes 0 or 3. `atan2f`
requires `(mask & 3) == 3`; the other four exports test nonzero. RVAs are protected
by the pinned DLL SHA256. These masks simulate CPU startup; they do not prove
that CRT startup completed or that Unicorn implements the selected instructions.

[Microsoft documents](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/get-fma3-enable-set-fma3-enable?view=msvc-170)
that x64 CRT startup enables FMA3 when the CPU supports it. Therefore FMA3 is the
documented default on a supporting modern x64 CPU, unless the application disables
it. This probe does not measure any particular Windows machine's startup state.

## Observations and stopping boundary

`smoke_summary.json` contains 30 observations: five functions, two dispatch
settings, and three CPU selections (default, Haswell, Skylake client).
Inputs are 1.0 for unary functions and (1.0, 2.0) for binary functions.
Apple values come directly from `/usr/lib/libSystem.B.dylib` via ctypes.
These single-case rates describe only smoke inputs, not sampled accuracy:

| Function | FMA off / Apple | FMA on / Apple | FMA on / off | AMD comparisons |
|---|---|---|---|---|
| expf | 1/1 | unavailable: invalid FMA instruction | unavailable | not run |
| atan2f | 1/1 | 0/1 (untrusted result) | 0/1 | not run |
| sinf | 1/1 | unavailable: invalid FMA instruction | unavailable | not run |
| cosf | 1/1 | unavailable: invalid FMA instruction | unavailable | not run |
| powf | 1/1 | 1/1 (trivial base 1) | 1/1 | not run |

All three CPU models produce the same rows. Repetition is not extra input
coverage. FMA `expf(1)` stops at RVA `0xb83bc`, `vfnmadd231sd`; `sinf(1)` at
`0xbc0a8`, `vfmadd213sd`; `cosf(1)` at `0xb7cac`, `vfmadd213sd`. FMA `atan2f(1,2)`
returns `0x00000000`, versus non-FMA and Apple `0x3eed6338`. Its cause is
unresolved: do not interpret it as a real UCRT numerical result. `powf(1,2)` is
only an identity branch and does not establish working general FMA execution.

Two execution approaches failed to deliver a usable FMA oracle: default Unicorn
with the dispatch mask initialized, and explicit FMA-capable CPU model selection.
The second approach produced no new successful boundary. Work stops here under
the ticket's two-approach stop rule. An initial exploratory run that merely called
the setter left capability zero and exercised non-FMA twice; it is not counted as
FMA evidence and is superseded by the asserted-mask summary.

AMD AOCL was cloned at `29fd054f383e6c5e2dec2fce781d5220059f1836` and source paths
inspected, but no AMD build or numerical comparison was run. The regenerable clone
was deleted. No 2,000,000-input runs, exhaustive plugin-range sweeps, near-zero
sweeps, or paper worst-case comparisons were performed. No bit-exact Mac feasibility
conclusion is established for any of the five functions.

Follow-up: qualify an emulator with actual scalar FMA/VEX support (including a
known-answer atan2 smoke check), or supply independently validated instruction-level
semantics with correct rounding. Then implement and validate UCRT error/TLS/import
paths against native Windows before the randomized raw-bit corpus. Port pinned AMD
scalar source with explicit contraction settings and compare both UCRT modes and
Apple; retain first mismatches. Exhaustive float intervals containing zero involve
billions of representations, so budget/chunk those separately from random sampling.
No AEXCompat modification or fuzzer oracle swap is authorized by this probe.
