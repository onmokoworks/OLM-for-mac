status: done

summary:
- Implemented and qualified the reached errno/FLS imports without replacing any mathematical return value.
- Added in-process, bounded-memory, atomic-resume comparison of both UCRT modes, both AMD builds, and Apple x86_64.
- Completed every 2^32 pattern for expf/sinf/cosf, 10^8 pairs each for atan2f/powf, and 26 published paper pairs.
- Identified polynomial/reduction differences in trig and three distinct powf mismatch causes; no AMD patch was written.
- No plugin, AEXCompat, fuzzer-oracle, ledger, release-gate, MAIN, or Microsoft-binary changes.

facts:

Environment and implementation:
- Branch `orch/F27c-ucrt-math-exhaustive`; macOS 15.7.2 (24G325), arm64 host, x86_64 executables under Rosetta; Apple clang 17.0.0 (clang-1700.6.4.2).
- DLL version 10.0.28000.2705, SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`; used directly from `/Users/onmk/.cache/olm-emu/ucrt/10.0.28000.2705/ucrtbase.dll`.
- AMD commit `29fd054f383e6c5e2dec2fce781d5220059f1836`, unmodified optimized scalar C expf/sinf/cosf/powf and reference scalar C atan2f. Off = contraction disabled, **not** all FMA disabled; explicit fused operations remain. Apple = x86_64 libSystem, not arm64 libm.
- `memory_pressure` before the pilot: 45% system-wide memory free. Scratch was 119 MiB at the first measured disk check, far below 5 GiB. No large result arrays: cumulative counts/buckets and at most 2000 witnesses per pair are held in memory. Unary sweeps ran serially; the short binary sweeps overlapped expf in a second process, then the serial runner resumed their completed checkpoints without rerunning inputs. One brief diagnostic build/check overlapped those two sweeps; this exceeded the worker's two-process build/emulator limit transiently. Subsequent build/verification work overlapped at most one sweep.
- Two independently relocated DLL images preserve the two FMA states in one process. MXCSR starts at 0x1f80. Output comparisons are exact bits, including signed zeros and NaN payload/sign; no tolerances.
- Unary order is every unsigned input word from 0 through 0xffffffff. Binary input index n uses SplitMix64(n XOR 0xf27c), low/high halves as the two arguments. Chunk size 2^24; cumulative checkpoint is fsync'd then atomically renamed. Runner verifies executable/AMD/DLL hashes before resume. Counters and the global first-2000 cap survive restart.

Stub boundary and qualification:
- Initial `expf(100)` with a single fake block returned for every FLS index faulted at RVA 0x3b1c0. Disassembly supplied a new boundary: FLS stores an app-state **index** as well as a thread-data **pointer**. Returning the pointer as the state index caused the invalid table lookup. This was corrected by modeling the two slots, not by altering a mathematical output.
- Pinned startup state: 0x13a4f0 = FLS slot 0 (app-state value zero); 0x13a4f4 = slot 1 (zeroed fake thread-data block). `_errno` at 0x46070 uses state stride 0x3c8 and errno offset 0x20. The encoded-null user-matherr pointer at 0x13bc30 is initialized from cookie 0x13a480; `__acrt_has_user_matherr` at 0x3b1a4 decodes it. No math instructions/tables are rewritten.
- Only `GetLastError`, `SetLastError`, `FlsGetValue` are bound to benign ms_abi stubs. State is thread-local; all other imports retain named abort thunks. Unexpected FLS indices fail closed. No FlsAlloc/FlsSetValue/Tls* import was reached, so none was implemented speculatively.
- `boundaries.py`: 25 cases / 50 native calls, exit 0, **zero native aborts**, five independent non-FMA Unicorn import boundaries remain as historical evidence. This does not pretend Unicorn's aborting error paths are numerical references.
- `qualify_errors.py`: MPFR 4.2.2, precision 200, **10/10** previously aborting mode/input calls pass IEEE/MPFR class checks. Both modes: expf(42c80000) = 7f800000; sinf/cosf(7f800000) = ffc00000; powf(bf800000,3f000000) = ffc00000; powf(00000000,bf800000) = 7f800000. Domain NaNs have sign 1 and fraction 400000. IEEE does not prescribe that exact NaN sign/payload.
- `error_state.c`: all ten calls preserve last-error sentinel 12345678; errno is 34 for overflow/pole and 33 for domain errors. Totals: GetLastError 20, SetLastError 20, FlsGetValue 30.
- `qualify.py --count 100000`: **500000/500000** non-FMA results exact against Unicorn, zero mismatches, no first mismatch. `sanity.py`: 500000 FMA samples, zero MPFR bound violations. Existing F27b sampled outputs and first-mismatch files reproduce unchanged.
- `check_sweep.py`: five functions × 4096 inputs × five engines agree with independent streamed calls; all ten pair counts, both marginal exponent-bucket tables and first witnesses agree. Uninterrupted and resumed checkpoints/CSVs are byte-identical. Binary tests include exceptional inputs.
- `sh tools/ucrt_math_probe/rosetta/reproduce_f27c.sh > orchestra/state/F27c-ucrt-math-exhaustive/reproduce.log 2>&1`: exit 0 for qualification, sample comparisons, restart checks, errno-state checks and 26 paper pairs / 130 engine results. Later-added diagnostics were also run individually with exact result-file comparisons.

- Final `reproduce_f27c.sh --full`: exit 0. All five complete sweep CSV sets reproduce byte-for-byte from the atomic checkpoints, with processed counts/bucket sums/witness caps checked. Full numerical sweeps had already completed; this final invocation verified restart/idempotence rather than spending another full sweep runtime. The subsequently added cosine diagnostic also passes and reproduces its retained JSON exactly.

- Cleanup: removed scratch executables, AMD build products/source checkout, paper checkout and MPFR venv; logs/checkpoints/data remain (51 MiB). No started background process remains. Committed result artifacts total 901523 bytes, including their SHA256 manifest; no Microsoft or AMD binaries are staged.

Sweep measurements:
All runs exit 0; zero aborts/signals. Counts below are **mismatches**, not matches. All ten pairs are retained. O = UCRT non-FMA; F = UCRT FMA; A = Apple; D0/D1 = AMD contraction-off/fast.

| Pair | expf / 2^32 | sinf / 2^32 | cosf / 2^32 | atan2f / 10^8 | powf / 10^8 |
|---|---:|---:|---:|---:|---:|
| O/F | 1 | 44232 | 18018 | 0 | 0 |
| O/A | 305178 | 3344140 | 3430118 | 20364273 | 2742 |
| O/D0 | 8388606 | 35909448 | 35355952 | 1595 | 1727 |
| O/D1 | 8388607 | 35909448 | 35355952 | 1595 | 1727 |
| F/A | 305179 | 3304072 | 3425432 | 20364273 | 2742 |
| F/D0 | 8388607 | 35876564 | 35337938 | 1595 | 1727 |
| F/D1 | 8388606 | 35876564 | 35337938 | 1595 | 1727 |
| A/D0 | 8693784 | 36942712 | 36532258 | 20362678 | 2697 |
| A/D1 | 8693785 | 36942712 | 36532258 | 20362678 | 2697 |
| D0/D1 | 1 | 0 | 0 | 0 | 0 |

Timing (seconds; pilot is 2^24 inputs, unary pilot covers only the cheapest first patterns):

| Function | Pilot | Linear projection before full run | Actual complete sweep |
|---|---:|---:|---:|
| expf | 0.673004 | 172.289 | 504.277526 |
| sinf | 0.632224 | 161.849 | 305.067253 |
| cosf | 1.051210 | 269.110 | 323.025153 |
| atan2f | 1.690883 | 10.078 | 7.437732 |
| powf | 3.662617 | 21.831 | 21.983543 |

Cumulative reached-import counts (both UCRT images):

| Function | GetLastError | SetLastError | FlsGetValue |
|---|---:|---:|---:|
| expf | 6117020726 | 6117020726 | 8157360134 |
| sinf | 8 | 8 | 12 |
| cosf | 8 | 8 | 12 |
| atan2f | 0 | 0 | 0 |
| powf | 251675948 | 251675948 | 354907480 |

First O/D0 mismatches (unary second word is zero):

| Function | Inputs | O / D0 |
|---|---|---|
| expf | 7f800001 00000000 | 7fc00001 / 7f800001 |
| sinf | 3a1285ff 00000000 | 3a1285ff / 3a1285fe |
| cosf | 3a544395 00000000 | 3f7ffffb / 3f7ffffa |
| atan2f | ffbd5d56 7fe6dcbc | 7fe6dcbc / fffd5d56 |
| powf | 56363937 c052da19 | 00000000 / 00000001 |

Exponent regions (biased field E; normal unbiased exponent = E−127, signs combined):
- sinf O/D0: every bucket E=116..254 has mismatches; no E=255 mismatch. 628770 mismatches have |x|<0.5 and therefore no reduction; bucket 126 adds 559428 and straddles pi/4. O/F differs only at E=150, 44232 inputs (magnitude [2^23,2^24)).
- cosf O/D0: E=116..254 except 120,121; 29692 mismatches have |x|<0.5. F/D0: every E=122..254, with 11678 below 0.5. O/F has 18014 differences in E=116..119 and four more in E=156,231; no nonfinite mismatches.
- powf O/D0: base E=0..255, exponent-argument E=124..150. Excluding NaN inputs, the base spans E=0..254 and exponent argument E=124..140 (sparse; exact missing buckets and counts are in regions.json and compressed buckets). These include subnormal bases and both output-underflow and ordinary finite rounding paths.
- atan2f O/D0: 1594 NaN differences plus one finite case in input buckets E=0 and E=13. Expf mode-matched O/D0 and F/D1 have only E=255 mismatches; cross-mode finite mismatch is in E=133.
- Final evidence: 13084901888 sweep inputs across the five functions, 65424509440 engine calls, plus 130 paper-case calls. Retained CSVs preserve all counts, both per-argument exponent marginals and up to the first 2000 mismatches per pair; compressed results directory is approximately 952 KiB before final metadata additions. No per-case numerical corrections were applied.


Published worst cases:
- Source: https://gitlab.inria.fr/zimmerma/math_accuracy, commit `c2b897fb393ed8df33452b225953ccd2003cd389`, `latex/glibc244.tex`, binary32 atan2/pow table rows, including both library columns. `paper-inputs.json` retains source SHA256 and line numbers. 26 table pairs (including repeated inputs) produce 130 results across five engines, retained separately from the random counts. Each function has 13 table rows: atan2f has 0 UCRT/AMD mismatches and 4 UCRT/Apple mismatches; powf has 2 UCRT/AMD and 1 UCRT/Apple mismatch (same counts for both modes/builds). This identifies the paper/corpus that F27b left unresolved; it does not claim an unpublished complete search corpus.

Disassembly/source comparison and diagnostics:
- sinf direct branch: UCRT non-FMA RVAs 0xbbcd0–0xbbcec use double 1/6 for the cubic; AMD `src/optimized/sinf.c` uses float32 `ONE_BY_SIX`. At input 3a1285ff, UCRT = 3a1285ff and AMD = 3a1285fe. A diagnostic evaluation reproduces both values with no reduction.
- UCRT sin degree-9 coefficients are at 0x10f910..0x10f928, evaluated at 0xbbd00..0xbbd50 / FMA 0xbc050..0xbc084. AMD uses a degree-7 minimax polynomial with different coefficients. At input bee5220e, direct evaluation reproduces UCRT bedd8f93 / AMD bedd8f92. Thus a reduction-only explanation is refuted by concrete no-reduction witnesses.
- UCRT cos degree-10 coefficients at 0x10f8e8..0x10f900 differ from AMD's degree-8 minimax polynomial. UCRT non-FMA evaluation is at 0xb7b20..0xb7b70, FMA at 0xb7c30..0xb7c7c. AMD cos's `COS_SMALL` bit threshold is 3c000000 (=2^-7); its comment saying 2^-13 is not the executed value. At 3a544395, UCRT0 evaluates the full polynomial and returns 3f7ffffb, while UCRT1 and AMD use the small-input quadratic and return 3f7ffffa. The diagnostic reproduces all three; no reduction is involved.
- Reduction boundaries differ: UCRT non-FMA sin 4b742400 (RVA 0xbbd79), FMA sin 4b800456 (0xbc095), non-FMA cos 48f42400 (0xb7965), FMA cos 4f490fdb (0xb7c95); AMD sin/cos 4c000000. UCRT SSE reduction has a cancellation-dependent correction using further pi/2 pieces (sin 0xbbddb..0xbbe24); AMD uses its two-piece fused Cody–Waite path and its own integer Payne–Hanek helper.
- `reduction_probe.c` invokes the actual UCRT non-FMA sin reduction helper at 0xbafc0 and the unmodified AMD header on four large inputs. All quadrant indices agree; three residuals are bit-identical. For 7f7fffff the residuals are -0x1.191cfe681daf6p-1 / -0x1.191cfe681daf7p-1. Both final sine outputs are bf0599b3, so this residual difference alone is **not** counted as a causal final-float mismatch. These four probes do not exhaustively partition the trig mismatches into reduction vs polynomial causes.
- Pow log-table reduction: UCRT 0xb9c0c (`shr rcx,44`) / 0xb9c10 (`adc ecx,0`) rounds the table index. AMD `calculate_log` masks 0x007f8000 and truncates; its extra rounding-bit code is commented out. All 257 used log-table and reciprocal-table entries match bit-for-bit (AMD reciprocal storage also has one trailing unused zero).
- The 1727 UCRT0/AMD-off powf mismatches fit entirely under the 2000 cap: 89 finite nonzero rounding differences, 881 zero/min-subnormal differences, 757 NaN sign differences. All 89 finite nonzero pairs have different rounded/truncated table indices. Read-only reconstruction using the unchanged DLL tables reproduces **89/89 UCRT and 89/89 AMD** outputs using their respective indices; there are no near-one-path cases among those 89. The paper pair 3f887ffa/44ac7ebb is also reproduced by the two index choices (UCRT 7f7ff8b2 / AMD 7f7ff8b4); the other paper mismatch 54738288/c063703b is the same zero/min-subnormal cutoff class.
- UCRT pow underflow comparison at 0xb9ca0 uses -0x1.9d1da00000000p+6 and branches to zero/error handling at 0xba2c0. AMD uses -0x1.9fe368p+6f. MPFR confirms all 881 observed zero/min-subnormal cases correctly round to 00000001; UCRT returns 00000000. Exact results range from 0.5001348037546144… to 0.9988482880500799… minimum-subnormal units. This is UCRT behavior to preserve for compatibility, not a stubbed replacement.
- All 757 pow NaN differences are exactly a sign-bit flip, with a negative NaN base and odd integer exponent. AMD's zeroinfnan(x) branch applies its odd-exponent sign adjustment to `x*x` even for NaNs; UCRT preserves the original NaN sign on these inputs.
- atan2f's 1595 UCRT/AMD mismatches comprise 1594 NaN/NaN differences and one finite case: inputs 803c1252 / 0686decf, UCRT b8e40bc6, AMD/Apple/MPFR b8e40bc5. The finite input exponents are bucket 0 (subnormal) and 13. No all-finite-domain equivalence is claimed from the original 100k sample.
- The unique finite expf mode difference is c2890f89: UCRT0/AMD-off/Apple 0e0c39fc, UCRT1/AMD-FMA/MPFR 0e0c39fd. AMD expf returns a NaN input directly (`return x`); UCRT quiets signaling NaNs. The 8388606 nonfinite-bucket mismatches equal the two-sign signaling-NaN population.

inference:
- The narrow stubs plus correct startup state are sufficient for every input actually swept. This is not qualification of general Windows startup, user matherr callbacks, arbitrary threading, or native Windows execution. Numerical output bits are preserved; libc errno/exception semantics beyond the stated checks are not a conformance claim.
- For powf, three localized AMD changes are a plausible candidate to explain **all 1727 random-sweep mismatches and both paper mismatches**: rounded log index, UCRT-compatible underflow cutoff, and excluding NaNs from odd-exponent sign adjustment. The diagnostic explains every observed class; it does not prove equality over 2^64 pairs or justify claiming a tested patch. No patch was written.
- For sinf/cosf, both polynomial/coefficient differences and structurally different reduction paths exist. No single small polynomial or reduction tweak is established as sufficient for all mismatches. A future compatibility variant should reproduce both UCRT dispatch modes' evaluation order and reduction branches, then rerun the full sweep. The high-exponent mismatch counts alone do not assign causality to reduction; polynomial errors also occur after correct reduction.
- The F27b sample agreements for expf/atan2f were not general equivalence. Full-domain NaNs, one finite expf mode boundary and the finite atan2f subnormal witness make those limits concrete.

changed_files:
- `tools/ucrt_math_probe/rosetta/oracle.c`: narrow imports and pinned CRT state initialization.
- `sweep.c`, `run_sweep.sh`, `check_sweep.py`, `retain_full.py`, `check_full.py`, `summarize_regions.py`: chunked/resumable engine comparisons, retention and verification.
- `qualify_errors.py`, `error_state.c`, `paper_cases.py`, `inspect_paths.py`, `diagnose_pow.py`, `diagnose_sin.py`, `diagnose_cos.py`, `reduction_probe.c`, `check_underflow.py`, `check_finite_witnesses.py`: qualification and reproducible read-only diagnoses.
- `README.md`, `reproduce_f27c.sh`, `reproduce.sh`, `check_results.py`: documentation/current-vs-historical verification.
- `results-f27c/`: small compressed CSVs, exact counts, buckets, first witnesses, paper inputs/results and diagnostic evidence.
- `orchestra/reports/F27c-ucrt-math-exhaustive.md`.

verify:
```sh
mkdir -p orchestra/state/F27c-ucrt-math-exhaustive
sh tools/ucrt_math_probe/rosetta/reproduce_f27c.sh --full > orchestra/state/F27c-ucrt-math-exhaustive/reproduce-full.log 2>&1
rg 'PASS' orchestra/state/F27c-ucrt-math-exhaustive/reproduce-full.log
```
Expected: exit 0; qualification/sample/errno/paper/restart checks pass; full checker reports 4294967296 inputs each for expf/sinf/cosf and 100000000 each for atan2f/powf, all ten pairs/buckets/first-mismatch files exact. Without `--full`, the command performs the shorter qualification, restart and diagnostic checks. Runtime is machine/load dependent; retained timing fields are not numerical pass criteria. MPFR diagnostics intentionally retain UCRT-vs-correct-rounding differences.

For read-only static evidence (after dependencies are present):
```sh
"/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python" tools/ucrt_math_probe/rosetta/inspect_paths.py > orchestra/state/F27c-ucrt-math-exhaustive/paths.txt
```

next:
- Separate ticket: implement and qualify a UCRT-compatible AMD powf variant addressing the three observed paths; preserve intentional UCRT underflow behavior and NaN bits. Add targeted near-one, subnormal and boundary-pair coverage beyond uniform raw-bit sampling.
- Separate ticket: port UCRT trig polynomial/reduction dispatch, with the retained exponent buckets and first witnesses as diagnostics; require complete 2^32 replay before claiming equality.
- Investigate the atan2f subnormal witness and NaN operand priority, and expf signaling-NaN quieting. This ticket does not change any plugin or fuzzer oracle.
