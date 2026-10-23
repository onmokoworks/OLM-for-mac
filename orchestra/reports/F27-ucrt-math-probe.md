status: blocked

summary:
- Official Microsoft SDK x64 UCRT obtained and pinned.
- All five exports execute the non-FMA smoke case directly.
- FMA execution fails under default and explicit Haswell/Skylake Unicorn CPU models.
- Stop rule reached; AMD builds and large comparisons were not performed.
- No plugin, AEXCompat, oracle, ledger, or release gate changes.

facts:
- Host: arm64 macOS 15.7.2 (24G325); MAIN's existing Python venv, Unicorn 2.1.4, Capstone 5.0.7.
- `curl -fL --retry 2 https://api.nuget.org/v3-flatcontainer/microsoft.windows.sdk.cpp/10.0.28000.2705/microsoft.windows.sdk.cpp.10.0.28000.2705.nupkg -o /Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/sdk.nupkg` exited 0; output redirected to scratch/download.log.
- `"$PROBE_PY" tools/ucrt_math_probe/acquire.py` extracted `c/Redist/10.0.28000.0/ucrt/DLLs/x64/ucrtbase.dll`. The package contains no `libucrt.lib`; other SDK packages were not checked.
- DLL file version **10.0.28000.2705**, SHA256 **385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3**. Microsoft files reside only under `~/.cache/olm-emu/ucrt/10.0.28000.2705/`.
- `_set_FMA3_enable` RVA `0xd6800` reads capability RVA `0x13bdf4` and writes active mask RVA `0x13bdf0`. The probe seeds capability 3 and asserts active mask 0/3 after calling the setter. Startup is not executed. An initial setter-only experiment left capability zero and exercised non-FMA twice; it is superseded, not FMA evidence.
- `"$PROBE_PY" tools/ucrt_math_probe/probe.py` generated `smoke_summary.json`: 30 observations (5 functions × 2 modes × 3 CPU models). Each uses a fresh machine. Default, Haswell (19), Skylake client (21) have identical observations.
- FMA expf(1) stops at RVA `0xb83bc`, `vfnmadd231sd`; sinf(1) at `0xbc0a8`, `vfmadd213sd`; cosf(1) at `0xb7cac`, `vfmadd213sd`. All report `UC_ERR_INSN_INVALID`.
- First returned-bit discrepancy: FMA atan2f(`0x3f800000`, `0x40000000`) returns `0x00000000`; non-FMA and Apple return `0x3eed6338`. The FMA result is unqualified emulator output, not established native UCRT behavior.
- FMA powf(1,2) returns `0x3f800000`; this is only an identity branch.
- `git clone --depth 1 https://github.com/amd/aocl-libm-ose.git orchestra/state/F27-ucrt-math-probe/aocl` succeeded at `29fd054f383e6c5e2dec2fce781d5220059f1836`. Inspected `src/ref/atan2f.c` and `src/optimized/expf.c`; AMD was not built or compared.
- `"$PROBE_PY" tools/ucrt_math_probe/probe.py --check tools/ucrt_math_probe/smoke_summary.json` exited 0: `PASS: 30 smoke observations reproduce; status remains blocked`.
- No random, exhaustive plugin-range, dense-near-zero, or paper worst-case comparisons were run.
- Automatic approval review rejected a combined report/cleanup/commit shell call before execution because it contained `rm -rf`: “rm -f style commands are not permitted. Use a safer approach”. Report creation and commit were subsequently separated; status remains blocked.

Per-function smoke rates: each row is ONE unique input, repeated for three CPU selections. These are not large-corpus match rates.

| Function | UCRT off / Apple | UCRT on / Apple | UCRT on / off | UCRT off/on / AMD | AMD / Apple |
|---|---|---|---|---|---|
| expf | 1/1 (100%) | unavailable: instruction fault | unavailable | not run | not run |
| atan2f | 1/1 (100%) | 0/1 (0%; untrusted) | 0/1 (0%; untrusted) | not run | not run |
| sinf | 1/1 (100%) | unavailable: instruction fault | unavailable | not run | not run |
| cosf | 1/1 (100%) | unavailable: instruction fault | unavailable | not run | not run |
| powf | 1/1 (100%) | 1/1 (100%; identity) | 1/1 (100%; identity) | not run | not run |

inference:
- Two execution approaches fail to supply a usable FMA oracle: default Unicorn with initialized dispatch, and explicit FMA-capable CPU selection. The latter provides no new successful boundary. Stop under the ticket's two-approach rule.
- This installed emulator appears limited at scalar FMA execution. The atan2f zero result needs separate VEX/dispatch qualification; its root cause is unresolved.
- General bit-exact Mac feasibility remains **undetermined for all five functions**. Neither AMD lineage nor a trivial smoke match establishes equivalence.
- [Microsoft documents](https://learn.microsoft.com/en-us/cpp/c-runtime-library/reference/get-fma3-enable-set-fma3-enable?view=msvc-170) that CRT startup enables FMA3 on supporting x64 CPUs. It is therefore the documented default on a modern supporting CPU unless disabled by the app; native startup was not measured here.
- SDK redistributable identity need not equal a particular AE machine's System32 UCRT. See [Microsoft deployment guidance](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment?view=msvc-170).

changed_files:
- `tools/ucrt_math_probe/acquire.py`
- `tools/ucrt_math_probe/probe.py`
- `tools/ucrt_math_probe/README.md`
- `tools/ucrt_math_probe/smoke_summary.json`
- `orchestra/reports/F27-ucrt-math-probe.md`

verify:
```sh
PROBE_PY='/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python'
mkdir -p orchestra/state/F27-ucrt-math-probe
"$PROBE_PY" tools/ucrt_math_probe/acquire.py > orchestra/state/F27-ucrt-math-probe/acquire.log
"$PROBE_PY" tools/ucrt_math_probe/probe.py --check tools/ucrt_math_probe/smoke_summary.json
```
Expected: exit 0 and `PASS: 30 smoke observations reproduce; status remains blocked`.
This verifies reproduction of the blocker, not numerical conformance.

next:
- F27b: qualify scalar FMA/VEX execution, including a known-answer atan2f check, in a supporting emulator or independently validated generic instruction implementation. No output patches or host transcendental substitution.
- Qualify UCRT error/TLS/import paths against native Windows before arbitrary inputs. This minimal leaf loader has no OS stubs and aborts unsupported paths.
- Then build pinned AMD scalar functions on arm64 with explicit contraction settings; run requested raw-bit comparisons and preserve first mismatches. Exhaustive intervals containing zero involve billions of float representations and need separate chunking/budgets.
- Any AEXCompat change or fuzzer oracle swap belongs to a subsequent ticket after oracle qualification. No external emulator source was modified or rebuilt.
