# Rosetta UCRT numerical probe (F27b / F27c)

This independent probe executes the pinned Windows UCRT PE64 math exports under
Rosetta, comparing **raw float32 result bits** with AMD scalar C and Apple's
x86_64 libSystem. It is not a general Windows CRT or a plugin oracle replacement.
No Microsoft binaries are copied, downloaded, or committed. See the F27b/F27c
reports in `orchestra/reports/` for measured results and limitations.

The DLL SHA256 is
`385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3`
(version 10.0.28000.2705). `oracle.c` maps sections, applies DIR64 relocations,
and calls exports with `ms_abi`. No DLL startup runs. Capability RVA 0x13bdf4
is seeded to 3; the real `_set_FMA3_enable` sets the asserted active mask 0/3.
MXCSR starts at 0x1f80 (nearest-even, gradual underflow, masked exceptions).
The trusted image is RWX and import thunks RX. This is not an untrusted PE parser.

## Error state

F27c supersedes F27b's abort-all policy **only** for `GetLastError`,
`SetLastError`, and `FlsGetValue`. The first two use thread-local state. The
observed FLS slots are initialized as CRT startup would: RVA 0x13a4f0 names slot
0 (app-state index zero), and RVA 0x13a4f4 names slot 1 (zeroed fake thread-data
storage; state stride 0x3c8, errno offset 0x20). The user-matherr callback at
0x13bc30 is initialized to encoded NULL using the cookie at 0x13a480.
These are state initialization writes, not math-code or returned-value changes.
Other imports still abort with exit 86; unexpected FLS indices also fail closed.
No allocator or FLS/TLS setter was reached, so those imports remain aborting.

Every normal exit logs hit counts for each implemented import. `error_state.c`
checks that ten exceptional calls preserve a nonzero last-error sentinel and set
errno to 33/34. `qualify_errors.py` checks all five formerly aborting inputs in
both modes against MPFR/IEEE result classes. NaN sign/payload are recorded;
IEEE does not uniquely prescribe them. Existing 500k Unicorn and 500k FMA MPFR
sample checks remain reproducible. `results/` is historical F27b evidence;
`results-f27c/` is the new evidence, including the changed boundary outcomes.

## Build and verify

Run from the worktree root:

```sh
mkdir -p orchestra/state/F27c-ucrt-math-exhaustive
sh tools/ucrt_math_probe/rosetta/reproduce_f27c.sh > orchestra/state/F27c-ucrt-math-exhaustive/reproduce.log 2>&1
```

This builds x86_64 binaries, clones pinned AMD sources, installs gmpy2 in a local
scratch venv, and runs qualification, samples, the paper corpus, and restart
checks. Requires Rosetta, Xcode clang, internet for AOCL/gmpy2, and MAIN's
existing Unicorn/pefile/Capstone Python environment. `TMPDIR` stays in scratch.
The legacy `reproduce.sh` checks the historical samples with F27c boundary
expectations; it does not assert exhaustive coverage.

`reproduce_f27c.sh --full` also checks memory pressure, times 2^24 chunks, runs
all full sweeps, and compares retained evidence byte-for-byte. Allow substantially
more time than the cheap low-exponent unary pilot suggests. Keep scratch under
5 GiB; delete compiled binaries, AOCL checkout and venv when finished. No jobs
or worker pool is used. The sweep itself uses one process and bounded memory.

## Sweep and resumption

`sweep.c` includes the loader and maps two independent UCRT images, one per FMA
mode. It dlopens Apple and both AMD libraries in the same process. It enumerates
all 2^32 unary bit patterns in unsigned order (including signed zeros, infinities,
and every NaN payload). For binary functions it uses 100,000,000 SplitMix64
outputs: `mix(index XOR 0xf27c)`, low 32 bits as argument 0 and high 32 as argument
1, starting at index zero. This is random raw-bit coverage, not exhaustive pairs.

All ten engine pairs get exact mismatch counts, biased-exponent bucket counts
for both input arguments, and the first 2000 mismatches **globally per pair**.
Unary argument 1 is zero. Buckets combine signs; 0 means zero/subnormal, 255
means infinity/NaN. NaN sign/payload differences count as mismatches. No output
ULP tolerance or numerical repair is used. Each 2^24-input chunk atomically
replaces a cumulative checkpoint after fflush/fsync; restarting recomputes only
the unfinished chunk. Final CSVs are generated from that checkpoint. Checkpoints
are native structs for this build, not a portable interchange format.

`run_sweep.sh STATE` binds resumptions to executable, AMD library and DLL hashes;
use a fresh output directory after changing any engine. Do not run two writers
on the same function/checkpoint. `check_sweep.py` independently compares 4096
inputs/function against the streamed callers and verifies complete checkpoint,
count, bucket and witness equality across uninterrupted/resumed runs. The
binary test includes domain, underflow, overflow and NaN paths.

`retain_full.py` packages CSVs in deterministic gzip; `check_full.py` verifies
all bytes, processed counts, bucket sums, and witness caps. The retained
summary records timings, identities, RNG, and stub hits. Checkpoints are scratch.

## AMD and paper scope

AOCL commit `29fd054f383e6c5e2dec2fce781d5220059f1836`: optimized scalar C
expf/sinf/cosf/powf, reference scalar C atan2f, their tables and handlers. No ISA
dispatcher. Builds use `-ffp-contract=off` or `-ffp-contract=fast -mfma`.
**Off is not FMA-free**: explicit fma calls remain fused through libSystem.
Neither AMD source nor an AMD patch is committed.

`paper-inputs.json` identifies the Zimmermann math_accuracy commit and paper
source SHA256, retaining 26 binary32 atan2/pow table input pairs (including the
second library columns and repeated witnesses). `paper_cases.py` reproduces
extraction; `check_sweep.py` evaluates all 26 pairs on all five engines separately
from the random sweep. These are the published table cases, not a claim to have
exhausted the paper's unpublished search history.

`inspect_paths.py` emits the relevant UCRT disassembly and RIP-relative constants
from the local DLL. `diagnose_pow.py` compares log tables and reconstructs only
the finite log-table path as a read-only diagnostic. `check_underflow.py` measures
the observed powf zero/min-subnormal boundary with MPFR. Neither diagnostic
changes AMD, UCRT, or sweep results.

`diagnose_sin.py` and `diagnose_cos.py` reproduce no-reduction polynomial
witnesses; `reduction_probe.c` compares four actual large-argument reduction
residuals. These bounded diagnostics do not claim an exhaustive causal partition.
