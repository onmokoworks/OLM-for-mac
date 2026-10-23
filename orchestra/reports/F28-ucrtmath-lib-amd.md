status: blocked

summary:
- Numerical work completed: native arm64 expf is exact over all 2^32 inputs in both modes; atan2f/powf are exact over 10^8 pairs each in both modes.
- Expanded targeted sets pass, including all retained F27c witnesses, paper rows, NaN priority, subnormal and power boundaries.
- Completed exhaustive log2f and 10^8-input double sin/cos/exp/pow surveys plus representative plugin ranges; none of these AMD functions matches UCRT bit-for-bit.
- Fixed unsigned atan index negation, the pow underflow guard, and general pow NaN-selection/identity paths; no plugin or oracle changes.
- `blocked` is mandatory under the brief's rejected-tool clause: automatic review rejected one cleanup command. Cleanup was subsequently completed safely; no numerical or environmental blocker remains.

facts:

Environment and scope:
- Resumed branch `orch/F28-ucrtmath-lib-amd`, preserving previous commit `fa280b42`. Read AGENT_GUIDE.md, the F27c report, GOTCHAS, compatibility plan and relevant ledger matrix entries. Only ucrtmath and this report changed.
- Before testing, `memory_pressure | tail -5` reported 55% system-wide memory free. Apple clang 17.0.0 (clang-1700.6.4.2), target arm64-apple-darwin24.6.0. `file` confirms native producer = arm64 and PE comparator = x86_64.
- AMD source was cloned into ticket scratch and checked out at `29fd054f383e6c5e2dec2fce781d5220059f1836`; survey builder asserts the pin and a clean checkout. Existing AMD license headers and original source hashes remain; NOTICE records modifications. No additional AMD source was vendored for the survey.
- The existing, unmodified F27c PE loader loads DLL SHA256 `385a6d73a50063a4c760bdb2ee59e575de7ff350a2e3b214ea491d08358484f3` directly from the cache. Two independently relocated images select and check modes, with MXCSR 0x1f80. No Microsoft binary, code, or disassembly listing was added.
- Library builds use `-arch arm64 -O2 -ffp-contract=off -fno-fast-math`; FMA is explicit, as documented by the prior operation-boundary observations in README. Library sources have no OLM dependency. Only test code includes the existing PE loader.
- At most two mathematical workers ran concurrently. Full outputs streamed through bounded pipes, not disk arrays. Scratch measured 44 MiB during the campaigns, below 5 GiB.

Corrections and actual intermediate failures:
- Initial atan2f failure from the previous run: `00000001 / 00000001`, candidate `e12aaaab`, oracle `3f490fdb`, 650/9178 mismatches per mode. Converting unsigned `index` to double before negation reduced that same set to 0/0.
- Initial powf targeted run: 13/75095 mismatches per mode; first `00000001 / 3f800001`, oracle `00000000`, candidate `00000001`.
- Broadening the exponent-only guard from `>` to `>=` was a rejected trial: it exposed overflow errors, including `7f7fffff / 3f800000`, oracle `7f7fffff`, candidate infinity. The final code instead checks the underflow cutoff independently of the unchanged overflow guard.
- Explicit NaN selection removed dependence on arm64 signaling-operand priority. The initial base-first policy passed 75095 targets but failed 17/79201 expanded targets per mode. The new boundary was default negative NaN `ffc00000`: with exponent `7f800001`, oracle selects `7fc00001`, while unconditional base priority selected `ffc00000`. The final general selection rule gives a NaN exponent priority over the default negative NaN, otherwise retaining base priority.
- Identity-path observations include `powf(3f800000,7f800001) = 3fc00000` and `powf(ff800001,0) = 7fc00001`. These unusual return bits are preserved, not replaced with mathematically preferred outputs.
- `probe_nan.py`, using the existing Unicorn Probe without changing it, independently confirmed 8/8 newly observed non-FMA NaN boundary outputs against the native candidate, with zero faults/mismatches. Both Rosetta modes pass the expanded target set. `nan-unicorn.json` retains all eight observations.
- No two distinct hypotheses were refuted without a new boundary: the rejected broad guard exposed the maximum-finite overflow boundary; the rejected unconditional NaN priority exposed the default-negative-NaN boundary. No per-input expected-output table or tolerance was introduced.

Library validation:

| Function | Expanded targets | Target mismatches mode 0 / 1 | Full input count | Full mismatches mode 0 / 1 |
| --- | ---: | ---: | ---: | ---: |
| expf | 8128 | 0 / 0 | 4294967296 | 0 / 0 |
| atan2f | 13779 | 0 / 0 | 100000000 | 0 / 0 |
| powf | 79201 | 0 / 0 | 100000000 | 0 / 0 |

- First mismatch: none in any final library campaign. Unary order covers every unsigned word; binary order is SplitMix64(index XOR 0xf27c), low/high words as arguments, identical to F27c. Each input is compared in both modes.
- Targets include every retained F27c mismatch operand pair across all engine comparisons, all 26 published paper rows deduplicated as inputs, near-one/subnormal/exp-boundary windows, integer/half-integer powers and atan exponent-gap transitions.
- Exact commands: `sh ucrtmath/tests/reproduce.sh`; `python3 ucrtmath/tests/full.py atan2f powf`; `python3 ucrtmath/tests/full.py expf`; after the final NaN refinement, `python3 ucrtmath/tests/full.py powf`. All final commands exit 0. The last powf run reports 18.617 seconds.
- The expf exhaustive run preceded the final **powf-only** NaN refinement. Expf implementation and compilation flags were unchanged; this is per-function source evidence, not a claim that every full run used the final aggregate executable hash.
- `check_stream.py`: valid one-row stream exits 0; short, partial-record and empty streams each exit 2 as expected. Both producer/comparator exits and exact row count are checked by the full runner. Runs restart from the beginning rather than reusing unbound checkpoints.

Remaining-import survey:
- Commands: `python3 ucrtmath/tests/build_survey.py` then `python3 ucrtmath/tests/survey.py sin cos exp pow log2f`, both exit 0. An initial survey link lacked AMD's sincos table translation unit; adding the unmodified `sincos_tbl.c` resolved it. No AMD implementation was edited.
- O/F = UCRT non-FMA/FMA; D0/D1 = unmodified AMD optimized scalar C, x86_64 contraction-off/fast+mfma; A = Apple **native arm64** libSystem. Explicit upstream FMA operations remain in either AMD build, as in F27c. These are not Apple x86_64 measurements.
- All ten engine-pair counts, finite-input mismatch counts and first witnesses are retained for every dataset. Counts below are mismatches, including NaN sign/payload differences.

| Function/dataset | Inputs | O/F | O/D0 | F/D1 | O/A |
| --- | ---: | ---: | ---: | ---: | ---: |
| log2f/full | 4294967296 | 0 | 2148040603 | 2148007040 | 2147796930 |
| sin/random | 100000000 | 479094 | 2949046 | 2850835 | 2591969 |
| cos/random | 100000000 | 479676 | 2946116 | 2845882 | 2614059 |
| exp/random | 100000000 | 1366 | 225302 | 225451 | 37893 |
| pow/random | 100000000 | 1 | 275 | 267 | 26204347 |
| sin/ranges | 1048576 | 10798 | 61221 | 58356 | 55413 |
| cos/ranges | 1048576 | 10889 | 59304 | 56276 | 53995 |
| exp/ranges | 1048576 | 1516 | 255315 | 255269 | 5946 |
| pow/ranges | 1048576 | 1 | 541 | 522 | 1597 |

First O/D0 witnesses (raw bits, unary second argument unused):

| Function | a / b | UCRT0 / AMD-off |
| --- | --- | --- |
| log2f | `0000000000007145` / `0000000000000000` | `00000000c3062d27` / `00000000c3062d28` |
| sin | `e2e986a5196887fa` / `ff713a7e3b896565` | `bfe82f7dbfa8479a` / `bfe82f7dbfa84799` |
| cos | `f2cdc193c9bba04a` / `6abf5a467f89ea4f` | `bfdfbe3f6995962b` / `bfdfbe3f6995962a` |
| exp | `c037ca4caa45f296` / `169daed0dbf485a0` | `3dc9990ba0401fa4` / `3dc9990ba0401fa5` |
| pow | `4af491eedc5e5b0a` / `c0173ef560c4bc83` | `00021a62ea4eeb21` / `00021a62ea4eeb20` |

- Log2f full sweep: 4294967296 inputs, completed in 470.331 seconds; O/F has zero differences. O/D0 has 2139651996 finite-input differences, F/D1 2139618433. “Finite input” includes negative domain inputs whose results are NaNs; these counts are not a count of positive-domain approximation errors. The positive subnormal first witness `00007145` independently establishes a non-NaN numerical difference.
- Double random finite-input O/D0 / F/D1 mismatches: sin 2949046 / 2850835; cos 2946116 / 2845882; exp 225302 / 225451; pow 263 / 255. Pow total counts also include NaN operand differences.
- Double random words use independent SplitMix64 seeds `0xf28` and `0xf28 ^ 0x123456789abcdef0`. Range sets each contain 1048576 inputs: angles [-8*pi,8*pi], exp [-128,0], pow bases [0,1]/[0,4], exponents [0,16] with integer/half-integer [-16,16], plus 256 special pairs.
- Representative range motivation was read-only inspection of `mac/OLMDistanceGradation/OLMDistanceGradation.cpp:394`/`:423` (negative Gaussian exp), `mac/OLMBlur/OLMBlur.cpp:1339`/`:1346` (repeat powers/Gaussian exp), `mac/OLMDirectionalBlur/OLMDirectionalBlur.cpp:879` (angle sin/cos and squared projections), and KiraKira channel powers. These sampled ranges are not a complete original-AEX reachability or UI-range proof.

Evidence and cleanup:
- `python3 ucrtmath/tests/check_results.py`: all 15 final numerical JSON files match scratch results exactly. The independent eight-row Unicorn evidence and development-boundary history are retained separately.
- Final build SHA256: native `94292e7102bbdba36e5750075e6d20a5d9e823fabc6fb1cf1567e6b8f5f26d39`; comparator `e9ce6a5fcabf60c35a0f9dd78b2007dbecef684c23785ade60db3e1552ae9bcd`; library `eb01beb2a7421b67c5c1196e6356e6bb87179524e3915c90039c04982369a9b9`. `identity.json` records final source, executable, DLL and corpus hashes.
- Automatic review rejected the combined command `cat .../full-expf.json; rm -rf ucrtmath/tests/__pycache__` with: “rm -f style commands are not permitted. Use a safer approach”. It did not execute. The read was repeated separately and the generated `.pyc` files were explicitly unlinked, then the empty directory removed. This recovered cleanup rejection is why the report has the brief-mandated `status: blocked`, despite completed numerical work; no additional permission is needed.

- Final cleanup removed the pinned AMD checkout and both regenerable build directories. Scratch remaining: 1858174 bytes; retained result artifacts: 22578 bytes, below 5 MB. All started worker processes exited. Logs, input text and numerical results remain.

inference:
- Expf is bit-exact for the complete binary32 domain in the tested two modes/environment. Atan2f/powf are qualified for the stated random and targeted corpora, not all 2^64 pairs or all rounding/exception modes. errno/exception side effects are outside this standalone return-bit library's claim.
- The observed unsigned conversion, cutoff placement and NaN selection rules explain the exposed failures at their causal operations. The independent Unicorn NaN checks support that these odd cases are UCRT behavior rather than an arm64 or Rosetta-only artifact.
- No remaining surveyed AMD function is a drop-in UCRT replacement. Recommend disassembly-guided behavioral analysis/port work for log2f and double sin/cos/exp, alongside already-known sinf/cosf. Double pow is much closer, so first diagnose its retained finite/subnormal/NaN witnesses for a small AMD-derived variant; do not assume the float fixes transfer.

changed_files:
- `ucrtmath/src/{atan2f.c,powf.c}`: causal corrections described above; other library code retained from the prior commit.
- `ucrtmath/{README.md,NOTICE}`: current validation scope and modifications.
- `ucrtmath/tests/{native.c,compare.c,targeted.py,reproduce.sh}`: expanded inputs and fail-closed stream checks.
- `ucrtmath/tests/{full.py,build_survey.py,survey.py,survey_native.c,survey_compare.c}`: bounded serial campaigns and five-engine remaining-import survey.
- `ucrtmath/tests/{check_stream.py,check_results.py,probe_nan.py,manifest.py}`: stream rejection checks, evidence verification, independent NaN checks and identities.
- `ucrtmath/tests/results/*.json`: actual counts, first witnesses, hashes and diagnostic observations.
- `orchestra/reports/F28-ucrtmath-lib-amd.md`.

verify:
From this worktree, rebuild and rerun all requested campaigns (sequentially):
```sh
state="$PWD/orchestra/state/F28-ucrtmath-lib-amd"
mkdir -p "$state"
export TMPDIR="$state"
sh ucrtmath/tests/reproduce.sh > "$state/recheck-targeted.log" 2>&1
python3 ucrtmath/tests/check_stream.py > "$state/recheck-stream.log" 2>&1
python3 ucrtmath/tests/full.py > "$state/recheck-full.log" 2>&1
git clone https://github.com/amd/aocl-libm-ose "$state/amd-source" > "$state/recheck-clone.log" 2>&1
git -C "$state/amd-source" checkout 29fd054f383e6c5e2dec2fce781d5220059f1836 >> "$state/recheck-clone.log" 2>&1
python3 ucrtmath/tests/build_survey.py > "$state/recheck-build-survey.log" 2>&1
python3 ucrtmath/tests/survey.py > "$state/recheck-survey.log" 2>&1
python3 ucrtmath/tests/check_results.py
PYTHONDONTWRITEBYTECODE=1 '/Users/onmk/Documents/Projects/Personal/OLM as/tools/emulation/.venv/bin/python' ucrtmath/tests/probe_nan.py > "$state/recheck-nan.json"
cmp ucrtmath/tests/results/nan-unicorn.json "$state/recheck-nan.json"
```
Expected: every command exits 0; 15 numerical evidence files reproduce exactly, all library mismatch counts are zero, all eight Unicorn NaN cases match. Survey mismatch counts are expected/nonzero as above. Timing fields and platform-dependent executable hashes are not numerical pass criteria. Clone is required after cleanup; if an identical clean pinned checkout already exists, reuse it.

next:
- Orchestrator review and separate integration ticket; no plugin integration was performed.
- Remaining-import tickets: log2f, sinf/cosf, double sin/cos/exp behavioral ports; focused double pow mismatch diagnosis.
- Broader binary-function coverage and complete AEX argument-range/reachability qualification remain outside the finite random/representative-range evidence. No release/AE-exact promotion is implied.
