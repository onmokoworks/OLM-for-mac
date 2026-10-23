# F27b Rosetta UCRT leaf oracle

This is a **qualified sampled leaf oracle, not a full-domain Windows CRT**.
It loads the pinned F27 PE64 DLL at an arbitrary mmap base, copies sections,
applies DIR64 relocations, resolves named exports, and binds each IAT slot to
an executable, named abort thunk. DLL SHA256 is checked before parsing. No
DllMain, CRT startup, Wine, OLM plugin code, or host transcendental substitution
is used. This is intentionally a loader for one trusted pinned DLL, not an
untrusted/general PE parser. The image is RWX; import thunks become RX.

`oracle.c` builds for x86_64 and calls through `ms_abi` function pointers. It
sets MXCSR to 0x1f80, seeds capability 3, calls the real FMA setter, and checks
active mask 0/3. Its five functions are expf, atan2f, sinf, cosf, powf. Each
input line contains two raw float32 hex words (the second is ignored for unary
functions); each output line contains one raw result word. Import failures
exit 86 with import name/function/inputs on stderr. Signals terminate with
diagnostics, never produce replacement values. No double exports are exposed.

Run from the worktree root:

```sh
mkdir -p orchestra/state/F27b-ucrt-math-rosetta
sh tools/ucrt_math_probe/rosetta/reproduce.sh > orchestra/state/F27b-ucrt-math-rosetta/reproduce.log 2>&1
tail -n 1 orchestra/state/F27b-ucrt-math-rosetta/reproduce.log
```

Expected: `PASS: retained qualification, MPFR, boundary, and sample comparisons
reproduce; full-domain status remains blocked`. Requires the F27 pinned DLL,
Rosetta, Xcode clang, MAIN's existing Unicorn/pefile/Capstone environment,
Python with venv support, and internet for pinned AOCL/gmpy2 acquisition.
All commands are serial. `TMPDIR` is the ticket scratch directory.

The fixed seed is 0xF27B. 100,000 shared inputs per function comprise expf
uniformly sampled on [-80,80], powf with positive bases 2^U(-10,10) and
exponents U(-8,8), and raw finite float32 pairs for the trig functions and
atan2f. Inputs are rounded to float32 before any engine sees them. This is
explicitly **not uniform sampling of every function's entire bit domain**.
MPFR uses 200-bit precision and measures absolute error divided by the ULP
at the exact-result approximation (minimum spacing 2^-149). The supplied
bounds are tested directly, not used as a bit-match tolerance.

`build_amd.py` uses unmodified AOCL commit
29fd054f383e6c5e2dec2fce781d5220059f1836: optimized scalar C expf/sinf/cosf/powf,
reference scalar C atan2f, supporting tables and error handlers. It bypasses
AOCL's ISA dispatcher. Both builds target x86_64, one with `-ffp-contract=off`
and one with `-ffp-contract=fast -mfma`. **Contraction-off is not FMA-free**:
explicit `fma()` in AOCL's Payne–Hanek reduction remains fused via Apple
libSystem in that build. The FMA build can lower it to hardware instructions.
No AOCL source modifications or numerical replacements are made. `apple.c`
also dispatches direct scalar AMD symbols when given a dylib path; otherwise
it uses Apple's x86_64 libSystem functions, all under Rosetta.

Results retain pairwise counts and the first 1000 mismatches **per pair per
function**. JSON `native` means UCRT non-FMA, `fma` means UCRT FMA. Timings
include process/streaming/checking overhead and are not kernel benchmarks.
No exhaustive unary run, 10^8-pair binary run, or paper worst-case corpus was
completed. The specific paper/worst-case list was not supplied or identified.

`boundaries.py` is the process-isolation fallback: every input/mode gets a fresh
native process, so an import abort does not lose subsequent evidence. It also
replays non-FMA cases in F27's Unicorn loader with IAT traps that stop at the
first import. Five inputs reach GetLastError in both engines; isolation
contains the failure but supplies no math result. Hence full-domain bit-match
rates cannot be supplied by this abort-on-import oracle. A follow-up must
qualify Windows error/TLS behavior or explicitly define coverage excluding
aborted inputs before doing the large sweeps. Never count aborts as matches.
