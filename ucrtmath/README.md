# ucrtmath — incomplete F28 candidate

**Not qualified for integration.** The first targeted run found 650 atan2f
mismatches in each mode. Work stopped under the ticket's zero-mismatch rule.
No exhaustive sweep, random sweep, or remaining-import survey was performed.

The standalone library has no OLM includes. It exports `ucrt_expf(x, mode)`,
`ucrt_atan2f(y, x, mode)`, and `ucrt_powf(x, y, mode)`, with `UCRT_NOFMA` and
`UCRT_FMA`. Apple clang builds native arm64 with contraction disabled. Explicit
`fma` calls choose fused arithmetic; no fast-math or compiler contraction is used.
Only raw return bits are in scope, under round-to-nearest and gradual underflow.
errno, exception flags, alternate rounding modes, and invalid mode values are
not qualified.

Build (from the repository root):

```sh
sh ucrtmath/build.sh orchestra/state/F28-ucrtmath-lib-amd/build
```

The build creates `libucrtmath.a`; callers include `ucrtmath/include/ucrtmath.h`.
For a standalone checkout, any explicit output directory can replace that path.
The test harness has an OLM test-only dependency on the existing qualified F27c
loader and paper inputs, neither of which is linked into the library.

Reproduce the current failure:

```sh
sh ucrtmath/tests/reproduce.sh
```

Expected exit 1 at atan2f. Results are written under the ticket scratch directory:
expf: 4,129 inputs, 0 mismatches per mode; atan2f: 9,178 inputs, 650 mismatches
per mode. First atan2f input `00000001 00000001`: oracle `3f490fdb`, candidate
`e12aaaab`. Retained result JSON is under `tests/results/`.

The arithmetic at `src/atan2f.c`'s table reduction currently includes `-index*u`
where `index` is unsigned. Inference: unsigned negation wraps before conversion
to double. This is a concrete candidate for the next ticket to fix and verify;
it was not corrected after the mandatory mismatch stop. Do not treat any
unexecuted function or input domain as passing.

`tests/native.c` can generate exhaustive expf words (`expf sweep 4294967296`)
or deterministic SplitMix64 pairs (`atan2f sweep 100000000` or
`powf sweep 100000000`), and streams 4,096 records per block. Each record is
four little-endian uint32 words: arguments a/b and candidate mode 0/1 results.
The x86_64 comparator loads two independent oracle images and compares raw bits
for each mode, retaining counts and one witness. At most two processes run.
These full runs have **not** been executed; resume/checkpoint support and full
stream-length validation remain to be added before a long campaign.

## Source and operation provenance

AMD source identity and original hashes are in `upstream.json`; license and
local changes are in `NOTICE`. Data arrays retain AMD values. Integer-backed
tables use memcpy-based conversion to avoid cross-translation-unit type aliasing.

Read-only UCRT observations checked the intended fused-operation boundaries:

- expf: range-reduction subtraction, two polynomial multiply/add operations,
  and final table multiply/add (RVAs b83bc, b83e7, b83f0, b8406). The initial
  scaling multiply remains separate from integer rounding.
- powf: two Horner multiply/add operations for log (ba3fb/ba404); reduction
  subtraction (ba45d); two Horner operations and table reconstruction
  (ba472/ba47b/ba49d). Near-one dispatch returns to the non-FMA exp path
  (ba5ab → b9c8e). The candidate retains the AMD near-one expression.
- atan2f: table-index formation, ratio numerator/denominator, cubic subtraction,
  and the small-ratio polynomial (399f8, 39a1b/39a20/39a3d,
  39ae0/39ae9/39af6). Exponents are taken after float-to-double widening;
  x NaNs have priority over y NaNs.

These are operation observations, not a proof of equivalence. No Microsoft
machine code, disassembly listing, or extracted constants are vendored.
