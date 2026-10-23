# ucrtmath

The `ms/` additions are **OLM-internal**, derived from UCRT behavior/disassembly,
and **must not be published standalone**. They provide `ucrt_sinf`, `ucrt_cosf`,
and `ucrt_log2f`; see [their provenance and validation](ms/README.md). This
restriction applies to the combined library built by `build.sh`. The AMD-derived
sources retain their separate attribution in `NOTICE`.

The requested expf exhaustive and atan2f/powf random campaigns pass in both
modes. Targeted results and the remaining-import survey are recorded in
`tests/results/` and the F28 report. Binary-function sampling is not a proof
over all 2^64 input pairs; integration is reserved for a separate ticket.

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
loader, retained witnesses and paper inputs, none of which is linked into the
library. No loader, plugin or release-gate files are changed.

Run targeted validation, including all retained F27c witnesses and paper pairs:

```sh
sh ucrtmath/tests/reproduce.sh
```

Run the complete campaigns (serial; two worker processes at most):

```sh
python3 ucrtmath/tests/full.py
```

This compares every expf input word and 100,000,000 SplitMix64 pairs each for
atan2f and powf, in both modes, against the unmodified qualified PE loader.
Each stream is bounded to 4,096 records; both process exits, exact input count,
and truncated records are checked. No complete output arrays are retained.
Runs restart from the beginning; they do not reuse unchecked checkpoints.
The required DLL is loaded from the existing cache, never distributed here.

For the survey only, clone AMD into the ticket scratch directory as `amd-source`,
check out the pinned commit in `upstream.json`, then run:

```sh
python3 ucrtmath/tests/build_survey.py
python3 ucrtmath/tests/survey.py
```

Survey engines are UCRT non-FMA/FMA, native Apple arm64, and unmodified AMD
x86_64 contraction-off/fast (explicit upstream FMA remains in either build).
The survey does not add log2f or double functions to this library. It retains
all ten pair counts, finite-input mismatch counts and first witnesses.
Double sampling uses two deterministic SplitMix64 words per index (seeds
`0xf28` and `0xf28 ^ 0x123456789abcdef0`). The range corpus covers angles
[-8*pi,8*pi], negative exponential arguments [-128,0], pow bases [0,1]/[0,4]
and exponents [0,16] plus integers/half-integers [-16,16], and 256 special pairs.
These are representative domains suggested by Gaussian coefficients,
angle transforms, normalized/HDR channels and repeat-decay powers in the Mac
sources; they are not a complete AEX reachability or UI-range proof.

`python3 ucrtmath/tests/manifest.py` records source, binary, DLL and corpus hashes
before deleting regenerable scratch builds. All numerical comparisons use raw
bits, including NaN payloads and signed zeros, with no tolerance.

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
machine code or disassembly listing is vendored. The OLM-internal `ms/`
functional constants are separately documented in its README.

## Resume corrections

The resumed atan2f reduction converts its unsigned table index to double before
negation. Powf checks the observed underflow threshold outside the original
exponent-only overflow guard. It also implements explicit NaN bit selection:
base priority except that the default negative NaN yields to a NaN exponent,
and the observed signaling-NaN identity-path quieting. This avoids depending
on Apple arm64 NaN operand propagation. The latter includes UCRT's unusual
`powf(1, sNaN)` result: quieting the base bits yields `3fc00000`.
These are compatibility behaviors, not correctly-rounded-math claims.

The expanded targeted corpus includes every retained F27c mismatch input,
all 26 published paper rows (deduplicated as inputs), NaN sign/payload pairs,
near-one and normal/subnormal windows, underflow/overflow witnesses,
integer/half-integer powers, and atan exponent-gap transitions.
