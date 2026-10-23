status: blocked

summary:
- Built a pinned PE64 Rosetta loader that executes all five UCRT float exports in both FMA modes.
- Non-FMA qualification: 500,000/500,000 exact against Unicorn; FMA MPFR sanity: zero bound violations.
- Built pinned AMD scalar C in two contraction modes and retained all 10 pairwise sample comparisons.
- Full-domain coverage is blocked by mandatory import aborts; isolation and independent Unicorn replay confirm the boundary.
- Exhaustive unary / 100 million binary measurements and paper worst cases remain unperformed.

facts:
- Host: macOS 15.7.2 (24G325), arm64; native executables and AMD libraries compiled x86_64 and run under Rosetta. Apple clang 17.0.0 (clang-1700.6.4.2).
- DLL: 10.0.28000.2705, SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`; loaded directly from the pre-existing cache, never copied or committed.
- Capability RVA 0x13bdf4 is set to 3; real `_set_FMA3_enable` is called; active mask RVA 0x13bdf0 is asserted 0/3. MXCSR 0x1f80. No CRT startup.
- `clang -arch x86_64 -O2 -Wall -Wextra -Wno-deprecated-declarations .../oracle.c -o .../oracle`: exit 0 after replacing the unavailable public ucontext header with sys/ucontext.h. Initial compile failed at the public header requirement; no numerical hypothesis was implicated.
- Smoke: expf(1)=402df854, atan2f(1,2)=3eed6338, sinf(1)=3f576aa4, cosf(1)=3f0a5140, powf(1,2)=3f800000 in both modes. Rosetta FMA atan2f does not reproduce the F27 Unicorn zero result.
- `qualify.py --count 100000`: exit 0; every function 100,000/100,000 exact; no first mismatch. Domains and RNG are specified in README/source.
- `sanity.py`: exit 0; gmpy2 2.3.2, MPFR 4.2.2, precision 200 bits. The supplied ULP bounds are sanity bounds, never bit-match tolerances.

| Function | Unicorn/non-FMA exact | Qualification seconds | FMA max error (ULP) | Bound | MPFR seconds |
|---|---:|---:|---:|---:|---:|
| expf | 100000/100000 | 1.873704 | 0.500264135570 | 0.501 | 1.155757 |
| atan2f | 100000/100000 | 2.350185 | 0.533989835188 | 0.584 | 1.189620 |
| sinf | 100000/100000 | 2.015178 | 0.524959940518 | 0.530 | 1.124670 |
| cosf | 100000/100000 | 2.083815 | 0.526686386327 | 0.530 | 1.113156 |
| powf | 100000/100000 | 2.437493 | 0.500367903903 | 1.00 | 1.524914 |

- `memory_pressure`: 51% system-wide memory free before comparisons. Single-threaded, serial runs; no parallel emulator/build workers.
- `boundaries.py`: exit 0; 25 input cases, 50 native mode calls, 10 exit-86 import aborts; 5 independent non-FMA Unicorn cases reach the same GetLastError import. No native signals occurred. All details retained in results/boundaries.json.
- Aborting inputs in both modes: expf(42c80000); sinf(7f800000); cosf(7f800000); powf(bf800000,3f000000); powf(00000000,bf800000). Import: `api-ms-win-core-errorhandling-l1-1-0.dll!GetLastError`.
- Fallback 1: native per-input process isolation (`boundaries.py`) preserves subsequent cases but the affected calls still abort. Fallback 2: F27 Unicorn with named IAT traps independently stops at that same OS dependency; it supplies no fallback numerical answer.
- `git clone --depth 1 https://github.com/amd/aocl-libm-ose.git .../aocl`: exit 0, commit `29fd054f383e6c5e2dec2fce781d5220059f1836`.
- `build_amd.py`: exit 0; unmodified optimized scalar expf/sinf/cosf/powf and reference scalar atan2f plus their C tables/handlers, x86_64 `-ffp-contract=off` and `-ffp-contract=fast -mfma`. No dispatcher or vector implementations. Explicit AOCL fma calls remain fused in the off build; this label means contraction-off, not FMA-free.
- `compare_sample.py`: exit 0. Apple is x86_64 libSystem under Rosetta. All tables below are **only the 100,000 qualified samples/function**, not exhaustive/random-full-domain rates. Timings include subprocess and stream comparison overhead.

O = UCRT non-FMA; F = UCRT FMA; A = Apple; D0 = AMD contraction-off; D1 = AMD contraction-fast/FMA. Each cell is exact matches / 100000 (percentage).

| Function | O/F | O/A | O/D0 | O/D1 | F/A | F/D0 | F/D1 | A/D0 | A/D1 | D0/D1 | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| expf | 100000 (100.000%) | 99885 (99.885%) | 100000 (100.000%) | 100000 (100.000%) | 99885 (99.885%) | 100000 (100.000%) | 100000 (100.000%) | 99885 (99.885%) | 99885 (99.885%) | 100000 (100.000%) | 1.374294 |
| atan2f | 100000 (100.000%) | 79483 (79.483%) | 100000 (100.000%) | 100000 (100.000%) | 79483 (79.483%) | 100000 (100.000%) | 100000 (100.000%) | 79483 (79.483%) | 79483 (79.483%) | 100000 (100.000%) | 0.412544 |
| sinf | 99995 (99.995%) | 99906 (99.906%) | 99130 (99.130%) | 99130 (99.130%) | 99911 (99.911%) | 99135 (99.135%) | 99135 (99.135%) | 99114 (99.114%) | 99114 (99.114%) | 100000 (100.000%) | 0.353371 |
| cosf | 100000 (100.000%) | 99919 (99.919%) | 99159 (99.159%) | 99159 (99.159%) | 99919 (99.919%) | 99159 (99.159%) | 99159 (99.159%) | 99130 (99.130%) | 99130 (99.130%) | 100000 (100.000%) | 0.413947 |
| powf | 100000 (100.000%) | 99992 (99.992%) | 99984 (99.984%) | 99984 (99.984%) | 99992 (99.992%) | 99984 (99.984%) | 99984 (99.984%) | 99980 (99.980%) | 99980 (99.980%) | 100000 (100.000%) | 0.411685 |

First mismatches (raw hex words; unary second inputs are ignored):

| Function | Pair | Inputs | Outputs in pair order |
|---|---|---|---|
| expf | native / apple | c268a99a 00000000 | 1587be54 / 1587be55 |
| expf | fma / apple | c268a99a 00000000 | 1587be54 / 1587be55 |
| expf | apple / amd-off | c268a99a 00000000 | 1587be55 / 1587be54 |
| expf | apple / amd-fma | c268a99a 00000000 | 1587be55 / 1587be54 |
| atan2f | native / apple | 3696b1cc e2b87ab0 | 40490fdb / 40490fda |
| atan2f | fma / apple | 3696b1cc e2b87ab0 | 40490fdb / 40490fda |
| atan2f | apple / amd-off | 3696b1cc e2b87ab0 | 40490fda / 40490fdb |
| atan2f | apple / amd-fma | 3696b1cc e2b87ab0 | 40490fda / 40490fdb |
| sinf | native / fma | 4b387bd4 f87b3fce | bf61ba6a / bf61ba69 |
| sinf | native / apple | ec678b0d 9d7795f6 | bf083d1a / bf083d19 |
| sinf | native / amd-off | bee5220e 3590ff18 | bedd8f93 / bedd8f92 |
| sinf | native / amd-fma | bee5220e 3590ff18 | bedd8f93 / bedd8f92 |
| sinf | fma / apple | ec678b0d 9d7795f6 | bf083d1a / bf083d19 |
| sinf | fma / amd-off | bee5220e 3590ff18 | bedd8f93 / bedd8f92 |
| sinf | fma / amd-fma | bee5220e 3590ff18 | bedd8f93 / bedd8f92 |
| sinf | apple / amd-off | bee5220e 3590ff18 | bedd8f93 / bedd8f92 |
| sinf | apple / amd-fma | bee5220e 3590ff18 | bedd8f93 / bedd8f92 |
| cosf | native / apple | 6b874d5e f6b62cbb | 3f2af0f4 / 3f2af0f3 |
| cosf | native / amd-off | cc43326e 68c99190 | 3f349893 / 3f349892 |
| cosf | native / amd-fma | cc43326e 68c99190 | 3f349893 / 3f349892 |
| cosf | fma / apple | 6b874d5e f6b62cbb | 3f2af0f4 / 3f2af0f3 |
| cosf | fma / amd-off | cc43326e 68c99190 | 3f349893 / 3f349892 |
| cosf | fma / amd-fma | cc43326e 68c99190 | 3f349893 / 3f349892 |
| cosf | apple / amd-off | cc43326e 68c99190 | 3f349893 / 3f349892 |
| cosf | apple / amd-fma | cc43326e 68c99190 | 3f349893 / 3f349892 |
| powf | native / apple | 3ad5198a 4008d130 | 359276d9 / 359276da |
| powf | native / amd-off | 418d701a c0eea6d2 | 3008a876 / 3008a875 |
| powf | native / amd-fma | 418d701a c0eea6d2 | 3008a876 / 3008a875 |
| powf | fma / apple | 3ad5198a 4008d130 | 359276d9 / 359276da |
| powf | fma / amd-off | 418d701a c0eea6d2 | 3008a876 / 3008a875 |
| powf | fma / amd-fma | 418d701a c0eea6d2 | 3008a876 / 3008a875 |
| powf | apple / amd-off | 418d701a c0eea6d2 | 3008a876 / 3008a875 |
| powf | apple / amd-fma | 418d701a c0eea6d2 | 3008a876 / 3008a875 |

- The first 1000 mismatches per function/pair are committed as JSONL, and complete sample counts, worst MPFR inputs, and boundary observations as JSON. Input generation is committed. No Microsoft or AMD source/binaries are committed.
- No exhaustive unary shard or 10^8-pair binary sweep was run; no full-domain counts or rates are claimed. Paper identity/worst-case input list was not supplied or established. Double exports were not added.

- `sh tools/ucrt_math_probe/rosetta/reproduce.sh > orchestra/state/F27b-ucrt-math-rosetta/reproduce.log 2>&1`: exit 0; all retained observations and mismatch JSONL reproduced exactly (timings ignored).
- Regenerable native binaries, AMD build products, scratch AOCL checkout, and scratch MPFR venv removed after verification; logs and sampled data retained.

inference:
- Sample qualification supports using this loader for the tested import-free leaf domains. It does not establish arbitrary-input Windows CRT behavior, and forcing FMA masks does not qualify Windows startup dispatch.
- The native loader hypothesis succeeds for sampled leaf execution but fails as a total float-domain oracle: at least the recorded exceptional inputs require an OS service. Process isolation contains these errors without resolving them; independent emulator replay confirms the same boundary.
- Full-domain numerical comparison cannot obtain outputs for these cases while every import must abort. Enumerating and classifying all aborted inputs would be a different, incomplete-coverage measurement; no match count is assigned to an abort. Stopping after the loader plus isolation/emulator fallbacks, without substituting host math or inventing Windows OS semantics.
- Five sinf sample differences between FMA modes show that choosing a dispatch mode matters for bit-exact conformance. Sample AMD expf/atan2f equality is not proof of general equivalence.

changed_files:
- `tools/ucrt_math_probe/rosetta/`: loader, native Apple/AMD caller, pinned scalar build script, seeded qualification, MPFR sanity, isolated boundary replay, pairwise sample comparison, reproduction/check scripts, README and retained results.
- `orchestra/reports/F27b-ucrt-math-rosetta.md`
- No plugin, AEXCompat, release gate, ledger, MAIN checkout, or fuzzer oracle changes.

verify:
```sh
mkdir -p orchestra/state/F27b-ucrt-math-rosetta
sh tools/ucrt_math_probe/rosetta/reproduce.sh > orchestra/state/F27b-ucrt-math-rosetta/reproduce.log 2>&1
tail -n 1 orchestra/state/F27b-ucrt-math-rosetta/reproduce.log
```
Expected: exit 0; `PASS: retained qualification, MPFR, boundary, and sample comparisons reproduce; full-domain status remains blocked`. All commands/flags and dependencies are in the committed script. Timing fields are excluded from comparison; numerical observations and first-mismatch files must reproduce exactly.

next:
- Qualify the UCRT error/TLS path against native Windows and define whether a future oracle may implement the required Windows imports. This ticket deliberately leaves every import aborting.
- Then add an in-process chunked sweep interface with resumable counts, complete 2^32 unary patterns and 10^8 binary pairs, and identify/import the paper worst-case inputs. Preserve aborted-path coverage separately if abort policy is retained.
- Propose a fuzzer oracle swap only after that additional qualification; no swap is included here.
